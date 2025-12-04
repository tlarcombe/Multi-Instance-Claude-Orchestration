#!/bin/bash
# Multi-Instance Claude Orchestration - Installation Script
# This script sets up the queue system on a new machine

set -e  # Exit on error

echo "=================================="
echo "Multi-Instance Claude Orchestration"
echo "Installation Script"
echo "=================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration - Update these for your environment
WORKSPACE_BASE="/mnt/shared/claude_workspace"  # Your shared NFS mount point
INSTALL_DIR="$HOME"
CLAUDE_PATH="$HOME/.local/bin/claude"  # Path to your Claude installation

echo -e "${YELLOW}Step 1: Checking requirements...${NC}"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3 found: $(python3 --version)${NC}"

# Check if Claude is installed
if [ ! -f "$CLAUDE_PATH" ]; then
    echo -e "${YELLOW}Warning: Claude not found at $CLAUDE_PATH${NC}"
    echo "Please install Claude or update CLAUDE_PATH in install.sh"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✓ Claude found at $CLAUDE_PATH${NC}"
fi

echo ""
echo -e "${YELLOW}Step 2: Setting up shared workspace...${NC}"

# Check if workspace directory exists
if [ ! -d "$WORKSPACE_BASE" ]; then
    echo -e "${YELLOW}Creating workspace directories...${NC}"

    # Try to create the directory
    if mkdir -p "$WORKSPACE_BASE"/{tasks,results,logs} 2>/dev/null; then
        echo -e "${GREEN}✓ Created workspace at $WORKSPACE_BASE${NC}"
    else
        echo -e "${RED}Error: Cannot create $WORKSPACE_BASE${NC}"
        echo "Please ensure:"
        echo "  1. NFS storage is mounted at $WORKSPACE_BASE"
        echo "  2. You have write permissions"
        echo ""
        echo "To mount NFS storage:"
        echo "  sudo mkdir -p /mnt/shared"
        echo "  sudo mount -t nfs YOUR_NFS_SERVER:/path /mnt/shared"
        exit 1
    fi
else
    echo -e "${GREEN}✓ Workspace already exists at $WORKSPACE_BASE${NC}"

    # Ensure subdirectories exist
    mkdir -p "$WORKSPACE_BASE"/{tasks,results,logs}
fi

# Check write permissions
if [ ! -w "$WORKSPACE_BASE/tasks" ]; then
    echo -e "${RED}Error: No write permission to $WORKSPACE_BASE/tasks${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Workspace is writable${NC}"

echo ""
echo -e "${YELLOW}Step 3: Installing queue system files...${NC}"

# Copy files to home directory
if [ -f "claude_queue.py" ]; then
    cp claude_queue.py "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/claude_queue.py"
    echo -e "${GREEN}✓ Installed claude_queue.py${NC}"
else
    echo -e "${RED}Error: claude_queue.py not found in current directory${NC}"
    exit 1
fi

if [ -f "claude_worker.py" ]; then
    # Update Claude path in worker if needed
    if [ -f "$CLAUDE_PATH" ]; then
        sed -i "s|claude_path = \".*\"|claude_path = \"$CLAUDE_PATH\"|" claude_worker.py
    fi

    cp claude_worker.py "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/claude_worker.py"
    echo -e "${GREEN}✓ Installed claude_worker.py${NC}"
else
    echo -e "${RED}Error: claude_worker.py not found in current directory${NC}"
    exit 1
fi

# Optional: Copy test script
if [ -f "test_queue.py" ]; then
    cp test_queue.py "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/test_queue.py"
    echo -e "${GREEN}✓ Installed test_queue.py (optional)${NC}"
fi

echo ""
echo -e "${YELLOW}Step 4: Verifying installation...${NC}"

# Test that we can import the library
if python3 -c "import sys; sys.path.insert(0, '$INSTALL_DIR'); from claude_queue import ClaudeQueue; q = ClaudeQueue(); print('OK')" &> /dev/null; then
    echo -e "${GREEN}✓ Python library imports successfully${NC}"
else
    echo -e "${RED}Error: Cannot import claude_queue library${NC}"
    exit 1
fi

# Get hostname
HOSTNAME=$(hostname)
echo -e "${GREEN}✓ Hostname: $HOSTNAME${NC}"

# Test queue operations
echo ""
echo -e "${YELLOW}Step 5: Running basic tests...${NC}"

TEST_RESULT=$(python3 << 'EOF'
import sys
sys.path.insert(0, "$INSTALL_DIR")
from claude_queue import ClaudeQueue
import os

try:
    q = ClaudeQueue()

    # Test listing tasks (should not error)
    tasks = q.get_pending_tasks()
    print(f"✓ Can list tasks (found {len(tasks)} pending)")

    # Test log writing
    q._log("Installation test")
    print("✓ Can write to logs")

    print("SUCCESS")
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
EOF
)

if echo "$TEST_RESULT" | grep -q "SUCCESS"; then
    echo -e "${GREEN}$TEST_RESULT${NC}"
else
    echo -e "${RED}Tests failed:${NC}"
    echo "$TEST_RESULT"
    exit 1
fi

echo ""
echo -e "${GREEN}=================================="
echo "Installation Complete!"
echo "==================================${NC}"
echo ""
echo "Files installed to: $INSTALL_DIR"
echo "  - claude_queue.py"
echo "  - claude_worker.py"
echo ""
echo "Next steps:"
echo ""
echo "1. Submit a test task:"
echo "   python3 ~/claude_queue.py submit 'echo test' $HOSTNAME"
echo ""
echo "2. Process tasks (one-shot):"
echo "   python3 ~/claude_worker.py --once"
echo ""
echo "3. Run continuous worker:"
echo "   python3 ~/claude_worker.py"
echo ""
echo "4. For production, set up systemd service:"
echo "   See README.md for instructions"
echo ""
echo "Documentation: See README.md and QUEUE_SYSTEM_STATUS.md"
echo ""
