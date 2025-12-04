#!/usr/bin/env python3
"""
Claude Worker Script
Monitors task queue and executes tasks using local Claude instance
"""

import subprocess
import sys
import time
import argparse
from claude_queue import ClaudeQueue
import socket


def run_claude_command(command):
    """
    Execute a Claude command and return the result

    Args:
        command: Command string to pass to Claude

    Returns:
        (output, error_message) tuple
    """
    try:
        # Run Claude with the command
        # Use full path to claude executable
        claude_path = "claude"  # Or set to your Claude installation path
        result = subprocess.run(
            [claude_path, "--dangerously-skip-permissions", command],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode == 0:
            return result.stdout, None
        else:
            return None, f"Claude exited with code {result.returncode}: {result.stderr}"

    except subprocess.TimeoutExpired:
        return None, "Command timed out after 5 minutes"
    except Exception as e:
        return None, f"Error running Claude: {str(e)}"


def process_single_task(queue):
    """
    Check for pending tasks and process one if available

    Returns:
        True if a task was processed, False otherwise
    """
    hostname = socket.gethostname()

    # Get pending tasks for this host
    tasks = queue.get_pending_tasks(for_host=hostname)

    if not tasks:
        return False

    # Try to claim the first task
    task = tasks[0]
    task_id = task["id"]

    if not queue.claim_task(task_id):
        return False  # Someone else claimed it

    print(f"Processing task {task_id}: {task['command'][:60]}...")

    # Execute the task
    output, error = run_claude_command(task["command"])

    # Submit result
    if error:
        queue.submit_result(task_id, output or "", status="failed", error=error)
        print(f"Task {task_id} failed: {error}")
    else:
        queue.submit_result(task_id, output, status="completed")
        print(f"Task {task_id} completed successfully")

    return True


def worker_loop(queue, interval=5, max_iterations=None):
    """
    Main worker loop - continuously process tasks

    Args:
        queue: ClaudeQueue instance
        interval: Seconds to wait between checks
        max_iterations: Max iterations (None = infinite)
    """
    hostname = socket.gethostname()
    print(f"Claude worker started on {hostname}")
    print(f"Checking for tasks every {interval} seconds")
    print("Press Ctrl+C to stop\n")

    iteration = 0

    try:
        while True:
            if max_iterations and iteration >= max_iterations:
                break

            processed = process_single_task(queue)

            if not processed:
                time.sleep(interval)

            iteration += 1

    except KeyboardInterrupt:
        print("\nWorker stopped by user")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Claude task queue worker")
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Seconds between task checks (default: 5)"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Process one task and exit"
    )

    args = parser.parse_args()

    queue = ClaudeQueue()

    if args.once:
        if not process_single_task(queue):
            print("No tasks available")
            sys.exit(1)
    else:
        worker_loop(queue, interval=args.interval)
