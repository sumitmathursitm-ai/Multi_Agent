#!/usr/bin/env bash
set -euo pipefail

STREAMLIT_PORT="${PORT:-8501}"
API_PORT="${API_PORT:-8000}"

uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "$API_PORT" &

API_PID=$!

cleanup() {
  kill "$API_PID" 2>/dev/null || true
}

trap cleanup EXIT

streamlit run streamlit_app.py \
  --server.address=0.0.0.0 \
  --server.port="$STREAMLIT_PORT" \
  --server.headless=true \
  --browser.gatherUsageStats=false
