# Multi-Instance Claude Orchestration

A distributed task queue system for orchestrating multiple Claude AI instances across networked machines. This enables seamless collaboration between Claude instances running on different devices, with shared task management and result retrieval.

## Overview

This project demonstrates how multiple Claude instances can work together as a coordinated team, sharing tasks through a filesystem-based message queue. Perfect for distributed computing scenarios, multi-device workflows, or coordinating AI assistance across your infrastructure.

### Key Features

- **Distributed Task Queue**: Filesystem-based message queue with atomic operations
- **Multi-Machine Coordination**: Route tasks to specific machines or any available worker
- **Asynchronous Execution**: Non-blocking task submission with optional result waiting
- **Built-in Locking**: File-based locking prevents race conditions
- **Audit Trail**: Complete logging of all operations with timestamps and host tracking
- **Simple Python API**: Easy-to-use library for task submission and result retrieval

## Architecture

```
┌─────────────┐         ┌─────────────────────────────┐         ┌─────────────┐
│   Machine A │         │   Shared NFS Storage        │         │   Machine B │
│             │         │  /mnt/shared/claude_workspace│         │             │
│  Claude     │────────▶│    ├── tasks/               │◀────────│  Claude     │
│  Instance   │         │    ├── results/             │         │  Instance   │
│             │         │    └── logs/                │         │             │
└─────────────┘         └─────────────────────────────┘         └─────────────┘
      │                              │                                  │
      └──────────────────────────────┴──────────────────────────────────┘
                           Task Coordination
```

## Requirements

- **Python 3.7+**
- **Shared Filesystem**: NFS mount accessible from all machines
- **Claude AI**: Installed on each participating machine
- **SSH Access**: Passwordless SSH between machines (for remote worker management)

## Quick Start

### 1. Mount Shared Storage

On each machine, mount your shared NFS storage:

```bash
sudo mkdir -p /mnt/shared
sudo mount -t nfs NFS_SERVER:/shared/path /mnt/shared
```

Or add to `/etc/fstab` for automatic mounting:
```
NFS_SERVER:/shared/path /mnt/shared nfs defaults 0 0
```

### 2. Run Installation Script

```bash
./install.sh
```

This will:
- Create the shared workspace directory structure
- Copy queue library and worker files to your home directory
- Make scripts executable
- Run verification tests

### 3. Submit Your First Task

```python
from claude_queue import ClaudeQueue

queue = ClaudeQueue()
task_id = queue.submit_task(
    "What is your hostname?",
    target_host="pi-node-1"  # or None for any available host
)

print(f"Task submitted: {task_id}")
```

### 4. Process Tasks

On the target machine:
```bash
python3 ~/claude_worker.py --once
```

Or run continuously:
```bash
python3 ~/claude_worker.py --interval 5
```

### 5. Retrieve Results

```python
result = queue.get_result(task_id, wait=True, timeout=60)
print(result['result'])
```

## Installation

### Automated Installation

Use the provided installation script:

```bash
# On each machine in your cluster
./install.sh
```

### Manual Installation

1. **Create shared workspace**:
```bash
mkdir -p /mnt/shared/claude_workspace/{tasks,results,logs}
```

2. **Copy files to each machine**:
```bash
scp claude_queue.py claude_worker.py user@remote-machine:~/
ssh user@remote-machine "chmod +x ~/claude_queue.py ~/claude_worker.py"
```

3. **Verify Claude installation path** in `claude_worker.py`:
```python
claude_path = "/home/user/.local/bin/claude"
```

## Usage

### Submitting Tasks

**Python API:**
```python
from claude_queue import ClaudeQueue

queue = ClaudeQueue()

# Submit to specific host
task_id = queue.submit_task("Check system uptime", target_host="pi-node-1")

# Submit to any available host
task_id = queue.submit_task("Run diagnostics")

# Submit with metadata
task_id = queue.submit_task(
    "Analyze logs",
    target_host="logserver",
    metadata={"priority": "high", "category": "maintenance"}
)
```

**Command Line:**
```bash
python3 claude_queue.py submit "Task description" [target_host]
```

### Running Workers

**One-shot execution:**
```bash
python3 claude_worker.py --once
```

**Continuous worker (checks every 5 seconds):**
```bash
python3 claude_worker.py
```

**Custom interval:**
```bash
python3 claude_worker.py --interval 10
```

### Retrieving Results

**Python API:**
```python
# Non-blocking check
result = queue.get_result(task_id)

# Wait for result (with timeout)
result = queue.get_result(task_id, wait=True, timeout=60)

# Check task status
status = queue.get_task_status(task_id)  # 'pending', 'in_progress', 'completed', 'failed'
```

**Command Line:**
```bash
python3 claude_queue.py result <task_id>
```

### Listing Tasks

**Python API:**
```python
# List all pending tasks
tasks = queue.get_pending_tasks()

# List tasks for specific host
tasks = queue.get_pending_tasks(for_host="pi-node-1")
```

**Command Line:**
```bash
python3 claude_queue.py list [hostname]
```

## Production Deployment

### Systemd Service (Recommended)

Create `/etc/systemd/system/claude-worker.service`:

```ini
[Unit]
Description=Claude Task Worker
After=network.target

[Service]
Type=simple
User=user
WorkingDirectory=/home/user
ExecStart=/usr/bin/python3 /home/user/claude_worker.py --interval 5
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable claude-worker
sudo systemctl start claude-worker
sudo systemctl status claude-worker
```

### Monitoring

Check logs for your host:
```bash
tail -f /mnt/shared/claude_workspace/logs/$(hostname)_$(date +%Y%m%d).log
```

## API Reference

### ClaudeQueue Class

```python
ClaudeQueue(hostname=None)
```

**Methods:**

- `submit_task(command, target_host=None, metadata=None)` → task_id
- `get_pending_tasks(for_host=None)` → list of tasks
- `claim_task(task_id)` → bool
- `submit_result(task_id, result, status="completed", error=None)`
- `get_result(task_id, wait=False, timeout=60)` → result dict
- `get_task_status(task_id)` → status string
- `cleanup_old_tasks(days=7)`

## File Structure

```
/mnt/shared/claude_workspace/
├── tasks/                          # Task queue
│   └── task_<timestamp>_<id>.json
├── results/                        # Completed results
│   └── result_<timestamp>_<id>.json
└── logs/                          # Per-host logs
    └── <hostname>_<date>.log

~/
├── claude_queue.py                # Queue library
└── claude_worker.py               # Worker daemon
```

## Task Format

**Task File** (`task_*.json`):
```json
{
  "id": "1764870164_8434f43f",
  "command": "Check system uptime",
  "from_host": "control-node",
  "target_host": "pi-node-1",
  "timestamp": "2025-12-04T19:42:44.123456",
  "status": "pending",
  "metadata": {}
}
```

**Result File** (`result_*.json`):
```json
{
  "task_id": "1764870164_8434f43f",
  "result": "System has been running for 76 days...",
  "status": "completed",
  "error": null,
  "completed_by": "pi-node-1",
  "completed_at": "2025-12-04T19:42:59.768099"
}
```

## Example Use Cases

### 1. Distributed System Monitoring
```python
machines = ["server01", "server02", "server03"]
task_ids = []

for machine in machines:
    task_id = queue.submit_task(
        "Check disk usage and report if any partition is over 80% full",
        target_host=machine
    )
    task_ids.append(task_id)

# Collect results
for task_id in task_ids:
    result = queue.get_result(task_id, wait=True, timeout=30)
    print(f"{result['completed_by']}: {result['result']}")
```

### 2. Parallel Data Processing
```python
files = ["data1.csv", "data2.csv", "data3.csv"]

for file in files:
    queue.submit_task(
        f"Analyze {file} and generate summary statistics",
        metadata={"file": file}
    )
```

### 3. Multi-Stage Workflows
```python
# Stage 1: Data collection
collect_task = queue.submit_task("Collect sensor data", target_host="sensor-pi")
result = queue.get_result(collect_task, wait=True)

# Stage 2: Analysis (on more powerful machine)
analysis_task = queue.submit_task(
    f"Analyze this data: {result['result']}",
    target_host="analysis-server"
)
```

## Troubleshooting

### Workers not picking up tasks

1. Check NFS mount: `df -h | grep shared`
2. Verify permissions: `ls -la /mnt/shared/claude_workspace/tasks/`
3. Check Claude path in worker: Edit `claude_worker.py` line 28

### Tasks timing out

- Default timeout is 5 minutes (300 seconds)
- Adjust in `claude_worker.py`: `timeout=300`
- For long-running tasks, increase this value

### Stale lock files

```bash
# Remove lock files older than 10 minutes
find /mnt/shared/claude_workspace/tasks/ -name "*.lock" -mmin +10 -delete
```

### Cleanup old tasks

```python
from claude_queue import ClaudeQueue
queue = ClaudeQueue()
queue.cleanup_old_tasks(days=7)
```

## Performance Considerations

- **Polling Interval**: Lower intervals = faster response, higher I/O load
- **NFS Performance**: Local SSD cache can improve performance
- **Concurrent Workers**: Multiple workers can process tasks in parallel
- **Task Granularity**: Balance between many small tasks vs. few large tasks

## Security Notes

- Shared filesystem access means any machine can read/write all tasks
- Use filesystem permissions to restrict access if needed
- Tasks run with full Claude permissions (uses `--dangerously-skip-permissions`)
- Consider network isolation for production deployments

## Contributing

Contributions welcome! This project demonstrates:
- Distributed task queuing patterns
- Multi-agent AI coordination
- Filesystem-based synchronization
- Python subprocess management

## License

MIT License - See LICENSE file for details

## Tested Configurations

- **control-node**: Local control node (Python 3.13.7)
- **pi-node-1**: Raspberry Pi 4/5, 8GB RAM, Debian Bookworm
- **pi-node-2**: Raspberry Pi 5, 8GB RAM, NVMe storage, Debian Bookworm

All configurations use Claude 2.0.58 with shared NFS storage .

## Acknowledgments

Built with [Claude Code](https://claude.ai/code) - Anthropic's CLI for Claude AI.
