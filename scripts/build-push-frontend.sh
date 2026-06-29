#!/bin/bash
set -e
cd /home/enigma/kinox/projects/bank/ai-berkshire/web
docker build -t localhost:30500/mizan-frontend:latest . 2>&1 | tail -5
echo "FRONTEND_BUILD_DONE"
docker push localhost:30500/mizan-frontend:latest 2>&1 | tail -3
echo "FRONTEND_PUSHED"
