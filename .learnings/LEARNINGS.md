# Learnings

## 2026-03-15: Next.js trailing slash breaks rewrite proxy
- **Category:** best_practice
- **Context:** Frontend API calls with trailing slash (e.g. `/api/nx/clients/`) returned 308 redirect instead of proxying to FastAPI backend
- **Root cause:** Next.js default behavior redirects trailing slash URLs before rewrites are applied
- **Fix:** Add `skipTrailingSlashRedirect: true` to `next.config.ts`
- **Lesson:** When using Next.js rewrites as API proxy to FastAPI (which expects trailing slashes), always set `skipTrailingSlashRedirect: true`

## 2026-03-15: Port correction — project uses 3001 + 8001
- **Category:** correction
- **Context:** I initially used port 3000 for frontend, user corrected that this project uses 3001
- **Lesson:** Project Nexus canonical ports are Frontend=3001, Backend=8001. Always check AGENTS.md Network Config before assuming default ports
