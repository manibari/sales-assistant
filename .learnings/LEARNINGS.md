# Learnings

## 2026-03-15: Next.js trailing slash breaks rewrite proxy
- **Category:** best_practice
- **Context:** Frontend API calls with trailing slash (e.g. `/api/nx/clients/`) returned 308 redirect instead of proxying to FastAPI backend
- **Root cause:** Next.js default behavior redirects trailing slash URLs before rewrites are applied
- **Fix:** Add `skipTrailingSlashRedirect: true` to `next.config.ts`
- **Lesson:** When using Next.js rewrites as API proxy to FastAPI (which expects trailing slashes), always set `skipTrailingSlashRedirect: true`

## 2026-03-15: Port correction — project uses 3002 + 8002
- **Category:** correction
- **Context:** Went through 3 rounds of port changes (3000→3001→3002) before aligning with production Cloudflare Tunnel mapping
- **Lesson:** Dev ports should match production. Check global port registry and infrastructure.md before setting ports. Current: Frontend=3002, Backend=8002

## 2026-03-15: FastAPI TrailingSlashMiddleware causes 404 on sub-path routes
- **Category:** best_practice
- **Context:** Custom middleware blindly appended `/` to all `/api/` paths, but routes like `/needs-push`, `/reminders`, `/expiring` were defined without trailing slash → 404
- **Root cause:** `redirect_slashes=False` + middleware adding `/` = routes with no trailing-slash definition become unreachable
- **Fix:** Remove custom middleware, use FastAPI default `redirect_slashes=True`
- **Lesson:** Don't override FastAPI's built-in slash handling with custom middleware. The default behavior handles both with and without `/` correctly
