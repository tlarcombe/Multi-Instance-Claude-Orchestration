#!/usr/bin/env python3
"""
Deploy Claude Worker systemd services to all machines via queue system
Uses dynamic path detection based on hostname
"""

from claude_queue import ClaudeQueue
import time

def main():
    q = ClaudeQueue()

    machines = {
        "GRATHRPI01": "Nhad368pass",
        "grathrpi05": "Nhad368pass",
        "hathi": "51isNOTprime!",
        "winifred": "51isNOTprime!"
    }

    task_ids = {}

    print("Deploying Claude Worker systemd services to all machines...")
    print("=" * 60)

    for machine, sudo_pass in machines.items():
        task_description = f"""
Please install the Claude Worker systemd service and timer:

1. Find the project directory (it should match your hostname):
   ```bash
   PROJECT_DIR=$(find ~/projects -maxdepth 1 -type d -name "*-local" | head -1)
   echo "Using project directory: $PROJECT_DIR"
   cd "$PROJECT_DIR"
   ```

2. Verify the service files exist:
   ```bash
   ls -la claude-worker.service claude-worker.timer
   ```

3. Install the systemd files (sudo password: {sudo_pass}):
   ```bash
   echo "{sudo_pass}" | sudo -S cp claude-worker.service /etc/systemd/system/
   echo "{sudo_pass}" | sudo -S cp claude-worker.timer /etc/systemd/system/
   echo "{sudo_pass}" | sudo -S chmod 644 /etc/systemd/system/claude-worker.service
   echo "{sudo_pass}" | sudo -S chmod 644 /etc/systemd/system/claude-worker.timer
   echo "{sudo_pass}" | sudo -S systemctl daemon-reload
   echo "{sudo_pass}" | sudo -S systemctl enable claude-worker.timer
   echo "{sudo_pass}" | sudo -S systemctl start claude-worker.timer
   ```

4. Verify the timer is running:
   ```bash
   echo "{sudo_pass}" | sudo -S systemctl status claude-worker.timer --no-pager
   echo "{sudo_pass}" | sudo -S systemctl list-timers claude-worker.timer --no-pager
   ```

5. Confirm:
   - Service installed: yes/no
   - Timer active: yes/no
   - Next run time: [display from systemctl output]

SUCCESS! Your Claude instance will now check for tasks every 2 minutes automatically.
"""

        task_id = q.submit_task(task_description, target_host=machine)
        task_ids[machine] = task_id
        print(f"  {machine}: Task {task_id} submitted")

    print("\nWaiting for results (timeout: 120 seconds)...")
    print("=" * 60)

    # Wait for results
    for machine in machines.keys():
        print(f"\nWaiting for {machine}...")
        task_id = task_ids[machine]
        result = q.get_result(task_id, wait=True, timeout=120)

        if result:
            print(f"\n{machine} DEPLOYMENT:")
            print("-" * 60)
            print(f"Status: {result.get('status')}")
            if result.get('result'):
                # Truncate long output
                result_text = result.get('result')
                if len(result_text) > 500:
                    print(f"{result_text[:500]}...[truncated]")
                else:
                    print(f"{result_text}")
            print("-" * 60)
        else:
            print(f"  {machine}: No result received (timeout)")

    print("\n" + "=" * 60)
    print("Deployment complete!")
    print("\nAll machines should now be checking for tasks every 2 minutes.")
    print("You no longer need to manually trigger workers!")

if __name__ == "__main__":
    main()
