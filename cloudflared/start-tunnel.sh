#!/bin/bash
# Start the Cloudflare Tunnel for Mizan
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Starting Mizan Cloudflare Tunnel..."
cloudflared tunnel \
  --config "${SCRIPT_DIR}/config.yml" \
  run mizan
