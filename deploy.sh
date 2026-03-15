#!/bin/bash
# deploy.sh — One-command deploy for sales-assistant on M1
# Usage: git pull && ./deploy.sh

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "=== Sales Assistant Deploy ==="
echo "Directory: $PROJECT_DIR"
echo ""

# --- 1. Check .env ---
if [ ! -f .env ]; then
    echo "[ERROR] .env not found. Copy from .env.example and fill in values:"
    echo "  cp .env.example .env"
    exit 1
fi

# --- 2. Python dependencies ---
echo "[1/4] Installing Python dependencies..."
pip3 install -r requirements.txt --quiet 2>&1 | tail -1
echo "  Done."

# --- 3. Frontend build ---
echo "[2/4] Installing frontend dependencies..."
cd frontend
npm ci --silent 2>&1 | tail -1
echo "[3/4] Building Next.js frontend..."
npm run build
cd "$PROJECT_DIR"
echo "  Done."

# --- 4. Stop existing processes ---
echo "[4/4] Starting services..."

# Kill previous instances if running
pkill -f "uvicorn backend.main:app" 2>/dev/null || true
pkill -f "next start" 2>/dev/null || true
sleep 1

# --- 5. Start backend + frontend ---
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"

# Backend: FastAPI on port 8002
cd "$PROJECT_DIR"
nohup python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8002 \
    > "$LOG_DIR/backend.log" 2>&1 &
echo "  Backend started (port 8002) — PID $!"

# Frontend: Next.js on port 3002
cd "$PROJECT_DIR/frontend"
nohup npx next start -p 3002 \
    > "$LOG_DIR/frontend.log" 2>&1 &
echo "  Frontend started (port 3002) — PID $!"

cd "$PROJECT_DIR"

echo ""
echo "=== Deploy Complete ==="
echo "  Frontend: http://localhost:3002"
echo "  Backend:  http://localhost:8002"
echo "  API docs: http://localhost:8002/docs"
echo "  Logs:     $LOG_DIR/"
echo ""
echo "To check status:  curl http://localhost:8002/api/health"
echo "To view logs:     tail -f $LOG_DIR/backend.log"
echo "To stop:          ./deploy.sh stop"

# --- Handle 'stop' command ---
if [ "${1}" = "stop" ]; then
    echo "Stopping services..."
    pkill -f "uvicorn backend.main:app" 2>/dev/null || true
    pkill -f "next start" 2>/dev/null || true
    echo "Services stopped."
    exit 0
fi
