#!/usr/bin/env python3
"""
Test script for Claude Queue system
Tests bidirectional communication between local and remote Claude instances
"""

import sys
import time
from claude_queue import ClaudeQueue

def test_local_to_remote():
    """Test sending a task from local to remote (grathrpi01)"""
    print("=" * 60)
    print("TEST 1: Local -> Remote (GRATHRPI01)")
    print("=" * 60)

    queue = ClaudeQueue()

    # Submit a task for grathrpi01
    command = "Please check the system uptime and report how long this system has been running. Use the 'uptime' command."
    print(f"\nSubmitting task to GRATHRPI01:")
    print(f"  Command: {command}")

    task_id = queue.submit_task(command, target_host="GRATHRPI01")
    print(f"  Task ID: {task_id}")

    # Wait for result
    print("\nWaiting for result (timeout: 60s)...")
    result = queue.get_result(task_id, wait=True, timeout=60)

    if result:
        print("\n✓ Result received!")
        print(f"  Status: {result['status']}")
        print(f"  Completed by: {result['completed_by']}")
        print(f"\nOutput:")
        print("-" * 60)
        print(result['result'])
        print("-" * 60)
        return True
    else:
        print("\n✗ No result received (timeout or worker not running)")
        print("\nTo complete this test, run on GRATHRPI01:")
        print("  python3 ~/claude_worker.py --once")
        return False


def test_remote_to_local():
    """Test sending a task from remote to local"""
    print("\n" + "=" * 60)
    print("TEST 2: Remote (GRATHRPI01) -> Local")
    print("=" * 60)

    import socket
    local_hostname = socket.gethostname()

    print(f"\nThis will require GRATHRPI01 to submit a task for: {local_hostname}")
    print("\nTo run this test:")
    print(f"  1. On GRATHRPI01, run:")
    print(f"     python3 ~/claude_queue.py submit 'Check Python version' {local_hostname}")
    print(f"  2. On this machine, run:")
    print(f"     python3 ~/projects/grathrpi01/claude_worker.py --once")
    print(f"  3. On GRATHRPI01, check result:")
    print(f"     python3 ~/claude_queue.py result <task_id>")


def test_list_tasks():
    """List all pending tasks"""
    print("\n" + "=" * 60)
    print("PENDING TASKS")
    print("=" * 60)

    queue = ClaudeQueue()
    tasks = queue.get_pending_tasks()

    if tasks:
        print(f"\nFound {len(tasks)} pending task(s):")
        for task in tasks:
            print(f"\n  Task ID: {task['id']}")
            print(f"  From: {task['from_host']}")
            print(f"  Target: {task.get('target_host', 'any')}")
            print(f"  Status: {task['status']}")
            print(f"  Command: {task['command'][:70]}...")
    else:
        print("\nNo pending tasks")


def main():
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "list":
            test_list_tasks()
        elif command == "remote-to-local":
            test_remote_to_local()
        elif command == "local-to-remote":
            test_local_to_remote()
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    else:
        # Run all tests
        print("CLAUDE QUEUE SYSTEM TEST SUITE\n")

        # First list any pending tasks
        test_list_tasks()

        # Test local to remote
        success = test_local_to_remote()

        # Show instructions for remote to local test
        if success:
            print("\n" + "!" * 60)
            print("NEXT STEPS")
            print("!" * 60)
            test_remote_to_local()


if __name__ == "__main__":
    main()
