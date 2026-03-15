Restart dev servers (frontend + backend). Verify ports are listening before reporting.

Steps:

1. Read `AGENTS.md` → Network Config table. Extract:
   - `FRONTEND_PORT`: the port number for "Next.js frontend"
   - `BACKEND_PORT`: the port number for "FastAPI backend"
2. Kill any process on those ports:
   ```
   lsof -ti:$FRONTEND_PORT | xargs kill -9 2>/dev/null
   lsof -ti:$BACKEND_PORT | xargs kill -9 2>/dev/null
   ```
3. Wait 1 second.
4. Start frontend:
   ```
   cd frontend && npm run dev &>/tmp/nexus-frontend.log &
   ```
5. Start backend (MUST source .env first):
   ```
   set -a && source .env 2>/dev/null && set +a && uvicorn backend.main:app --reload --port $BACKEND_PORT &>/tmp/nexus-backend.log &
   ```
6. Wait 5 seconds for servers to start.
7. Verify frontend: `lsof -iTCP:$FRONTEND_PORT -sTCP:LISTEN -t`
8. Verify backend: `curl -s http://localhost:$BACKEND_PORT/api/nx/clients/ | head -20`
9. Report status table (use actual port numbers from step 1):

| Service | Port | Status |
|---------|------|--------|
| Frontend (Next.js) | $FRONTEND_PORT | ✅ / ❌ |
| Backend (FastAPI) | $BACKEND_PORT | ✅ / ❌ |

10. If backend failed, show last 10 lines of `/tmp/nexus-backend.log`.
11. If frontend failed, show last 10 lines of `/tmp/nexus-frontend.log`.

IMPORTANT: Always read ports from AGENTS.md. Never hardcode port numbers.
