#!/usr/bin/env bash
# One-time setup for macOS/Linux/Git Bash. Run from the project root:  bash scripts/setup.sh
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] || { cp .env.example .env; echo "Created .env"; }
[ -f frontend/.env.local ] || { cp frontend/.env.example frontend/.env.local; echo "Created frontend/.env.local"; }
docker compose up -d --wait postgres redis
cd backend
[ -d .venv ] || python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate
pip install --upgrade pip
pip install -r requirements.txt
alembic upgrade head
cd ../frontend && npm ci
echo "Setup complete. Terminals: (backend) uvicorn app.main:app --reload --port 8000 | python -m app.worker | (frontend) npm run dev"
