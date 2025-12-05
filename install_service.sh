#!/bin/bash
# Install Claude Worker systemd service and timer

set -e

echo "Installing Claude Worker systemd service..."

# Copy service files to systemd directory
echo "$SUDO_PASS" | sudo -S cp claude-worker.service /etc/systemd/system/
echo "$SUDO_PASS" | sudo -S cp claude-worker.timer /etc/systemd/system/

# Set correct permissions
echo "$SUDO_PASS" | sudo -S chmod 644 /etc/systemd/system/claude-worker.service
echo "$SUDO_PASS" | sudo -S chmod 644 /etc/systemd/system/claude-worker.timer

# Reload systemd
echo "$SUDO_PASS" | sudo -S systemctl daemon-reload

# Enable and start the timer
echo "$SUDO_PASS" | sudo -S systemctl enable claude-worker.timer
echo "$SUDO_PASS" | sudo -S systemctl start claude-worker.timer

# Show status
echo ""
echo "✓ Installation complete!"
echo ""
echo "Service status:"
echo "$SUDO_PASS" | sudo -S systemctl status claude-worker.timer --no-pager || true
echo ""
echo "Next run:"
echo "$SUDO_PASS" | sudo -S systemctl list-timers claude-worker.timer --no-pager || true
echo ""
echo "To view logs:"
echo "  sudo journalctl -u claude-worker.service -f"
echo ""
echo "To manually trigger:"
echo "  sudo systemctl start claude-worker.service"
