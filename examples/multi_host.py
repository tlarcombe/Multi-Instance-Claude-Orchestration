#!/usr/bin/env python3
"""
Multi-host example: Send tasks to multiple machines and collect results
"""

import sys
sys.path.insert(0, '..')
from claude_queue import ClaudeQueue
import time

def main():
    # List of target hosts
    hosts = ["grathrpi01", "grathrpi05", "winifred"]

    queue = ClaudeQueue()

    print("Submitting tasks to multiple hosts...")
    print("="*50)

    # Submit tasks to each host
    task_map = {}
    for host in hosts:
        task_id = queue.submit_task(
            "Check your system uptime and report how long the system has been running.",
            target_host=host
        )
        task_map[task_id] = host
        print(f"Task {task_id} → {host}")

    print(f"\nSubmitted {len(task_map)} tasks")
    print("\nNote: You need to run workers on each machine:")
    for host in hosts:
        print(f"  ssh {host} 'python3 ~/claude_worker.py --once'")

    print("\n" + "="*50)
    print("Waiting for results (60s timeout)...")
    print("="*50)

    # Collect results
    results = {}
    for task_id, host in task_map.items():
        print(f"\nChecking {host}...", end=" ")
        result = queue.get_result(task_id, wait=True, timeout=60)

        if result and result['status'] == 'completed':
            results[host] = result
            print("✓")
        else:
            print("✗ (timeout or failed)")

    # Display results
    if results:
        print("\n" + "="*50)
        print("RESULTS")
        print("="*50)

        for host, result in results.items():
            print(f"\n{host}:")
            print("-" * 40)
            print(result['result'][:200])  # First 200 chars
            print()
    else:
        print("\nNo results received. Make sure workers are running!")

if __name__ == "__main__":
    main()
