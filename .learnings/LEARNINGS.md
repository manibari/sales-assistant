# Project Learnings

## best_practice — Use window.location.replace() for auth redirects after logout

**Date:** 2026-04-07

`router.push('/login')` from Next.js is unreliable immediately after clearing React state via setState(null). The component unmounts before navigation completes, leaving a blank page. Use `window.location.replace('/login')` for a synchronous hard redirect. Bonus: clears browser history so user can't go back to protected page.

---

## best_practice — gstack browse: avoid sleep, use wait --networkidle; re-import cookies each session

**Date:** 2026-04-07

The browse server has an idle timeout — `sleep N` between commands kills it. Use `$B wait --networkidle` instead. Cookies are NOT persisted between separate Bash tool calls. Solution: get JWT via `curl POST /auth/login`, save as browser cookie JSON, then `$B cookie-import <file>` at the start of each Bash block.

---

## knowledge_gap — Next.js App Router: nested layouts don't replace root layout

**Date:** 2026-04-07

`app/login/layout.tsx` nests INSIDE `app/layout.tsx`, not instead of it. Any sidebar in the root layout always appears on all pages. Correct pattern: use a client component (AppShell) with `usePathname()` to conditionally render the shell.
