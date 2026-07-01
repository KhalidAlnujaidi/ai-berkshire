#!/bin/bash
# Install cloudflared as a systemd service for Mizan
# Run with: sudo bash ai-berkshire/cloudflared/install-service.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing Mizan Cloudflare Tunnel service..."

# Copy service file
cp "${SCRIPT_DIR}/mizan-tunnel.service" /etc/systemd/system/mizan-tunnel.service

# Reload systemd
systemctl daemon-reload

# Enable and start
systemctl enable mizan-tunnel
systemctl start mizan-tunnel

sleep 3

# Check status
systemctl status mizan-tunnel --no-pager

echo ""
echo "✓ Mizan tunnel installed as systemd service"
echo "  Commands:"
echo "    sudo systemctl status mizan-tunnel"
echo "    sudo systemctl restart mizan-tunnel"
echo "    journalctl -u mizan-tunnel -f"
