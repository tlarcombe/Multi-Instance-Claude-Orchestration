# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

This project enables remote control and automation of Claude AI instances on remote machines. The primary use case is to command Claude on remote systems (like Raspberry Pi devices) to perform tasks and retrieve results.

## Remote Machine Access

### Active Claude Team Members

**pi-node-1:**
- **Hostname:** pi-node-1
- **Platform:** Raspberry Pi 4/5 (aarch64) running Debian Bookworm
- **Hardware:** 8GB RAM, 29GB SD card, 76+ day uptime
- **Claude Installation:** `/home/user/.local/bin/claude`
- **Queue System:** ✓ Operational

**pi-node-2:**
- **Hostname:** pi-node-2
- **Platform:** Raspberry Pi 5 (ARM Cortex-A76, aarch64) running Debian Bookworm
- **Hardware:** 8GB RAM, 458GB NVMe storage
- **Claude Installation:** `/home/user/.local/bin/claude`
- **Queue System:** ✓ Operational

**control-node (local):**
- **Hostname:** control-node
- **Platform:** Local machine
- **Claude Installation:** `/home/user/.local/bin/claude`
- **Queue System:** ✓ Operational

### Connecting to Remote Machines

Basic SSH connection (all machines use public key auth):
```bash
ssh pi-node-1 "command"
ssh pi-node-2 "command"
```

### Running Claude on Remote Machine

**CRITICAL:** When running Claude commands on remote machines, always use the `--dangerously-skip-permissions` flag to avoid interactive prompts:

```bash
ssh pi-node-1 "/home/user/.local/bin/claude --dangerously-skip-permissions 'task description'"
```

Without this flag, remote Claude instances will require interactive approval for certain operations, which will fail in non-interactive SSH sessions.

### Capturing Remote Output

To capture Claude's output from the remote machine:
```bash
ssh pi-node-1 "/home/user/.local/bin/claude --dangerously-skip-permissions 'command'" > local_output.txt
```

## Project Architecture

This repository serves as the control point for orchestrating remote Claude operations. Reports and outputs from remote machines are stored locally in this directory for analysis and tracking.

### Project Location
- **Local Directory:** `~/projects/pi-node-1`

### Directory Structure
- System reports from remote machines are stored with descriptive names (e.g., `pi-node-1_report1.txt`)

## Common Workflows

### Using the Queue System (Recommended)

The preferred method for multi-Claude coordination is the shared filesystem queue:

**Submit a task:**
```python
from claude_queue import ClaudeQueue
q = ClaudeQueue()
task_id = q.submit_task("Task description", target_host="pi-node-2")
```

**Process tasks on a machine:**
```bash
ssh pi-node-2 "cd /home/user && python3 claude_worker.py --once"
```

**Retrieve results:**
```python
result = q.get_result(task_id, wait=True, timeout=60)
```

See `QUEUE_SYSTEM_STATUS.md` for complete queue system documentation.

### Direct SSH Method (Legacy)

For simple one-off commands:
```bash
ssh pi-node-1 "/home/user/.local/bin/claude --dangerously-skip-permissions 'task'" > output.txt
```
