#!/usr/bin/env python3
"""
Claude Task Queue Library
Manages task exchange between multiple Claude instances via shared filesystem
"""

import json
import time
import uuid
import os
from datetime import datetime
from pathlib import Path
import fcntl
import socket

WORKSPACE = "/mnt/shared/claude_workspace"
TASKS_DIR = f"{WORKSPACE}/tasks"
RESULTS_DIR = f"{WORKSPACE}/results"
LOGS_DIR = f"{WORKSPACE}/logs"


class ClaudeQueue:
    """Manages task queue for distributed Claude instances"""

    def __init__(self, hostname=None):
        """Initialize queue with hostname identification"""
        self.hostname = hostname or socket.gethostname()
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure workspace directories exist"""
        for directory in [TASKS_DIR, RESULTS_DIR, LOGS_DIR]:
            Path(directory).mkdir(parents=True, exist_ok=True)

    def _atomic_write(self, filepath, data):
        """Write file atomically using temp file + rename"""
        temp_path = f"{filepath}.tmp.{uuid.uuid4()}"
        with open(temp_path, 'w') as f:
            json.dump(data, f, indent=2)
        os.rename(temp_path, filepath)

    def _lock_file(self, filepath, timeout=5):
        """Context manager for file locking"""
        class FileLock:
            def __init__(self, path, timeout):
                self.path = path
                self.timeout = timeout
                self.lockfile = None

            def __enter__(self):
                lockpath = f"{self.path}.lock"
                self.lockfile = open(lockpath, 'w')
                start_time = time.time()
                while True:
                    try:
                        fcntl.flock(self.lockfile.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                        return self
                    except IOError:
                        if time.time() - start_time > self.timeout:
                            raise TimeoutError(f"Could not acquire lock on {lockpath}")
                        time.sleep(0.1)

            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.lockfile:
                    fcntl.flock(self.lockfile.fileno(), fcntl.LOCK_UN)
                    self.lockfile.close()

        return FileLock(filepath, timeout)

    def submit_task(self, command, target_host=None, metadata=None):
        """
        Submit a new task to the queue

        Args:
            command: Command string for Claude to execute
            target_host: Optional specific host to target (None = any host)
            metadata: Optional dict of additional metadata

        Returns:
            task_id: Unique task identifier
        """
        task_id = f"{int(time.time())}_{uuid.uuid4().hex[:8]}"

        task = {
            "id": task_id,
            "command": command,
            "from_host": self.hostname,
            "target_host": target_host,
            "timestamp": datetime.now().isoformat(),
            "status": "pending",
            "metadata": metadata or {}
        }

        task_file = f"{TASKS_DIR}/task_{task_id}.json"
        self._atomic_write(task_file, task)

        self._log(f"Task submitted: {task_id}")
        return task_id

    def get_pending_tasks(self, for_host=None):
        """
        Get list of pending tasks

        Args:
            for_host: If specified, only return tasks for this host (or tasks with no target)

        Returns:
            List of task dicts
        """
        tasks = []
        for task_file in Path(TASKS_DIR).glob("task_*.json"):
            try:
                with open(task_file, 'r') as f:
                    task = json.load(f)

                # Check if task is for this host or any host
                if task.get("status") == "pending":
                    target = task.get("target_host")
                    if for_host is None or target is None or target == for_host:
                        tasks.append(task)
            except (json.JSONDecodeError, IOError):
                continue

        # Sort by timestamp
        tasks.sort(key=lambda t: t.get("timestamp", ""))
        return tasks

    def claim_task(self, task_id):
        """
        Claim a task for processing (atomic operation)

        Args:
            task_id: Task ID to claim

        Returns:
            True if successfully claimed, False if already claimed
        """
        task_file = f"{TASKS_DIR}/task_{task_id}.json"

        try:
            with self._lock_file(task_file):
                with open(task_file, 'r') as f:
                    task = json.load(f)

                if task.get("status") != "pending":
                    return False

                task["status"] = "in_progress"
                task["claimed_by"] = self.hostname
                task["claimed_at"] = datetime.now().isoformat()

                self._atomic_write(task_file, task)
                self._log(f"Task claimed: {task_id}")
                return True

        except (FileNotFoundError, TimeoutError):
            return False

    def submit_result(self, task_id, result, status="completed", error=None):
        """
        Submit result for a completed task

        Args:
            task_id: Task ID
            result: Result data (will be JSON serialized)
            status: "completed" or "failed"
            error: Optional error message if failed
        """
        result_data = {
            "task_id": task_id,
            "result": result,
            "status": status,
            "error": error,
            "completed_by": self.hostname,
            "completed_at": datetime.now().isoformat()
        }

        result_file = f"{RESULTS_DIR}/result_{task_id}.json"
        self._atomic_write(result_file, result_data)

        # Update task status
        task_file = f"{TASKS_DIR}/task_{task_id}.json"
        try:
            with self._lock_file(task_file):
                with open(task_file, 'r') as f:
                    task = json.load(f)

                task["status"] = status
                task["completed_at"] = datetime.now().isoformat()

                self._atomic_write(task_file, task)
        except (FileNotFoundError, TimeoutError):
            pass

        self._log(f"Result submitted: {task_id} - {status}")

    def get_result(self, task_id, wait=False, timeout=60):
        """
        Get result for a task

        Args:
            task_id: Task ID
            wait: If True, wait for result to appear
            timeout: Max seconds to wait if wait=True

        Returns:
            Result dict or None if not found
        """
        result_file = f"{RESULTS_DIR}/result_{task_id}.json"
        start_time = time.time()

        while True:
            if os.path.exists(result_file):
                try:
                    with open(result_file, 'r') as f:
                        return json.load(f)
                except (json.JSONDecodeError, IOError):
                    pass

            if not wait or (time.time() - start_time) > timeout:
                return None

            time.sleep(0.5)

    def get_task_status(self, task_id):
        """Get current status of a task"""
        task_file = f"{TASKS_DIR}/task_{task_id}.json"
        try:
            with open(task_file, 'r') as f:
                task = json.load(f)
                return task.get("status")
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def _log(self, message):
        """Write to log file"""
        log_file = f"{LOGS_DIR}/{self.hostname}_{datetime.now().strftime('%Y%m%d')}.log"
        timestamp = datetime.now().isoformat()
        with open(log_file, 'a') as f:
            f.write(f"{timestamp} - {message}\n")

    def cleanup_old_tasks(self, days=7):
        """Remove tasks and results older than specified days"""
        cutoff = time.time() - (days * 86400)

        for directory in [TASKS_DIR, RESULTS_DIR]:
            for filepath in Path(directory).glob("*.json"):
                if filepath.stat().st_mtime < cutoff:
                    filepath.unlink()
                    self._log(f"Cleaned up old file: {filepath.name}")


if __name__ == "__main__":
    # Simple CLI for testing
    import sys

    queue = ClaudeQueue()

    if len(sys.argv) < 2:
        print("Usage:")
        print("  claude_queue.py submit '<command>' [target_host]")
        print("  claude_queue.py list [for_host]")
        print("  claude_queue.py result <task_id>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "submit":
        task_command = sys.argv[2]
        target = sys.argv[3] if len(sys.argv) > 3 else None
        task_id = queue.submit_task(task_command, target)
        print(f"Task submitted: {task_id}")

    elif command == "list":
        for_host = sys.argv[2] if len(sys.argv) > 2 else None
        tasks = queue.get_pending_tasks(for_host)
        print(f"Pending tasks: {len(tasks)}")
        for task in tasks:
            print(f"  {task['id']}: {task['command'][:50]}...")

    elif command == "result":
        task_id = sys.argv[2]
        result = queue.get_result(task_id)
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No result found")
