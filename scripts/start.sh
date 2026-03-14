#!/usr/bin/env bash
# start.sh — Kill existing servers and start fresh. One command to rule them all.
#
# Usage:  ./scripts/start.sh
#         or: npm run start (if added to package.json)

set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "🔄 Stopping existing servers..."
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:8001 | xargs kill -9 2>/dev/null || true
sleep 1

echo "🚀 Starting frontend (Next.js :3000)..."
cd "$PROJECT_ROOT/frontend" && npm run dev &>/tmp/nexus-frontend.log &
disown

echo "🚀 Starting backend (FastAPI :8001 + Telegram webhook)..."
cd "$PROJECT_ROOT" && set -a && source .env 2>/dev/null && set +a
uvicorn backend.main:app --reload --port 8001 &>/tmp/nexus-backend.log &
disown

echo "⏳ Waiting for servers..."
sleep 3

# Verify
FRONTEND_OK=false
BACKEND_OK=false

if lsof -iTCP:3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
  FRONTEND_OK=true
fi
if lsof -iTCP:8001 -sTCP:LISTEN -t >/dev/null 2>&1; then
  BACKEND_OK=true
fi

echo ""
echo "=== Status ==="
$FRONTEND_OK && echo "✅ Frontend    http://localhost:3000" || echo "❌ Frontend    FAILED (check /tmp/nexus-frontend.log)"
$BACKEND_OK  && echo "✅ Backend     http://localhost:8001" || echo "❌ Backend     FAILED (check /tmp/nexus-backend.log)"
$BACKEND_OK  && echo "✅ Telegram    /api/nx/telegram/webhook"
echo ""
echo "Logs: /tmp/nexus-frontend.log, /tmp/nexus-backend.log"
