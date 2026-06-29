#!/bin/bash
set -e
cd /home/enigma/kinox/projects/bank/ai-berkshire

# Build backend with sharia_screener.py from tools/ 
docker build -t localhost:30500/mizan-backend:latest \
  -f backend/Dockerfile \
  backend/ \
  --build-context tools=./tools 2>&1 | tail -5

# Actually simpler: copy sharia_screener.py into build context
cp tools/sharia_screener.py backend/sharia_screener.py

docker build -t localhost:30500/mizan-backend:latest \
  -f backend/Dockerfile \
  backend/ 2>&1 | tail -5

echo "BACKEND_BUILD_DONE"

docker push localhost:30500/mizan-backend:latest 2>&1 | tail -3
echo "BACKEND_PUSHED"
