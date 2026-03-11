Kill and restart frontend and backend dev servers. Telegram bot runs as FastAPI webhook (no separate process needed).

Steps:
1. Kill any process on port 3000 (Next.js frontend)
2. Kill any process on port 8000 (FastAPI backend)
3. Start frontend: `cd frontend && npm run dev` in background, log to /tmp/nexus-frontend.log
4. Start backend: `set -a && source .env && set +a && uvicorn backend.main:app --reload --port 8000` in background, log to /tmp/nexus-backend.log (MUST source .env first for TELEGRAM_BOT_TOKEN etc.)
5. Wait 3 seconds, then verify both ports are listening with `lsof -iTCP:3000 -sTCP:LISTEN` and `lsof -iTCP:8000 -sTCP:LISTEN`
6. Report status to user (include Telegram webhook status: available at /api/nx/telegram/webhook)
