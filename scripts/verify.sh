#!/usr/bin/env bash
# Health check + smoke journey. Run from the project root with the venv active or present in backend/.venv.
set -euo pipefail
cd "$(dirname "$0")/.."
curl -fsS http://localhost:8000/api/v1/health && echo
curl -fsS http://localhost:8000/api/v1/health/ready && echo
cd backend
PY=python3; [ -x .venv/bin/python ] && PY=.venv/bin/python; [ -x .venv/Scripts/python.exe ] && PY=.venv/Scripts/python.exe
"$PY" scripts/smoke_journey.py
