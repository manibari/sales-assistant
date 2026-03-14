Restart dev servers (frontend + backend). Verify ports are listening before reporting.

Steps:

1. Kill any process on port 3000 and port 8001:
   ```
   lsof -ti:3000 | xargs kill -9 2>/dev/null
   lsof -ti:8001 | xargs kill -9 2>/dev/null
   ```
2. Wait 1 second.
3. Start frontend:
   ```
   cd frontend && npm run dev &>/tmp/nexus-frontend.log &
   ```
4. Start backend (MUST source .env first):
   ```
   set -a && source .env 2>/dev/null && set +a && uvicorn backend.main:app --reload --port 8001 &>/tmp/nexus-backend.log &
   ```
5. Wait 5 seconds for servers to start.
6. Verify frontend: `lsof -iTCP:3000 -sTCP:LISTEN -t`
7. Verify backend: `curl -s http://localhost:8001/api/nx/clients/ | head -20`
8. Report status table:

| Service | Port | Status |
|---------|------|--------|
| Frontend (Next.js) | 3000 | ✅ / ❌ |
| Backend (FastAPI) | 8001 | ✅ / ❌ |

9. If backend failed, show last 10 lines of `/tmp/nexus-backend.log`.
10. If frontend failed, show last 10 lines of `/tmp/nexus-frontend.log`.

Port reference: AGENTS.md → Network Config section.
