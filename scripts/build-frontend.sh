#!/bin/bash
set -e
cd /home/enigma/kinox/products/agent/ai-berkshire/web
docker build -t localhost:30500/mizan-frontend:latest . 2>&1 | tail -5
echo "BUILD_DONE"
docker push localhost:30500/mizan-frontend:latest 2>&1 | tail -3
echo "PUSH_DONE"
