#!/bin/bash
set -e
cd /home/enigma/kinox/products/agent/ai-berkshire/backend
docker push localhost:30500/mizan-backend:latest 2>&1
echo "BACKEND_PUSHED"
