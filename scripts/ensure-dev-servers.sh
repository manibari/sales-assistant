#!/usr/bin/env bash
# ensure-dev-servers.sh — idempotent check: start dev servers only if not running
# Called by Claude Code PostToolUse hook after Edit/Write

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Frontend (Next.js dev on port 3000)
if ! lsof -iTCP:3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
  cd "$PROJECT_ROOT/frontend" && npm run dev &>/tmp/nexus-frontend.log &
  disown
fi

# Backend (FastAPI uvicorn on port 8001) — matches frontend next.config.ts rewrite
if ! lsof -iTCP:8001 -sTCP:LISTEN -t >/dev/null 2>&1; then
  cd "$PROJECT_ROOT" && set -a && source .env 2>/dev/null && set +a && uvicorn backend.main:app --reload --port 8001 &>/tmp/nexus-backend.log &
  disown
fi
