#!/usr/bin/env bash
# One command to launch the draft assistant: FastAPI backend + Vite frontend.
# Usage:  ./scripts/dev.sh   then open http://localhost:5173
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ ! -x backend/.venv/bin/uvicorn ]; then
  echo "Backend venv missing. Create it with:"
  echo "  python3.11 -m venv backend/.venv && backend/.venv/bin/pip install -r backend/requirements.txt"
  exit 1
fi
if [ ! -d frontend/node_modules ]; then
  echo "Installing frontend deps…"
  (cd frontend && npm install)
fi

# Ensure the board is built so the API starts instantly.
backend/.venv/bin/python -m backend.run_pipeline >/dev/null 2>&1 || true

echo "Starting backend on :8000 and frontend on :5173 …"
backend/.venv/bin/uvicorn backend.api.app:app --port 8000 &
BACK=$!
(cd frontend && npm run dev) &
FRONT=$!

# Clean up both on Ctrl-C.
trap 'echo; echo "Shutting down…"; kill $BACK $FRONT 2>/dev/null || true' INT TERM
echo "Open http://localhost:5173  (Ctrl-C to stop)"
wait
