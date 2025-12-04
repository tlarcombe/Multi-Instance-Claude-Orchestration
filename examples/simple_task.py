#!/usr/bin/env python3
"""
Simple example: Submit a task and wait for result
"""

import sys
sys.path.insert(0, '..')
from claude_queue import ClaudeQueue

def main():
    # Create queue instance
    queue = ClaudeQueue()

    # Submit a simple task
    print("Submitting task...")
    task_id = queue.submit_task(
        "What is your hostname? Please respond with just the hostname.",
        target_host=None  # Any available host
    )
    print(f"Task ID: {task_id}")

    # Wait for result (timeout after 60 seconds)
    print("\nWaiting for result...")
    result = queue.get_result(task_id, wait=True, timeout=60)

    if result:
        print("\n" + "="*50)
        print("Result received!")
        print("="*50)
        print(f"Completed by: {result['completed_by']}")
        print(f"Status: {result['status']}")
        print(f"\nOutput:\n{result['result']}")
    else:
        print("\nNo result received (timeout or no worker available)")
        print("Make sure a worker is running:")
        print("  python3 claude_worker.py --once")

if __name__ == "__main__":
    main()
