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

## 2026-03-26: FOLLOWUP_PROMPT missing format placeholders
- **Category:** bug_discovery
- **Context:** `FOLLOWUP_PROMPT.format(current_json=..., user_msg=..., chat_history_section=...)` was called but the template had no `{current_json}` / `{user_msg}` / `{chat_history_section}` placeholders. Python's `str.format()` silently ignores missing placeholders — AI received zero context about the conversation.
- **Fix:** Added placeholders at end of prompt template.
- **Lesson:** Always verify format templates contain expected placeholders. `str.format()` with no matching `{}` is a silent no-op.

## 2026-03-26: Command priority in intent detection
- **Category:** bug_discovery
- **Context:** `detect_intent()` checked `has_active_conversation` first, returning FOLLOWUP before slash commands. `/done` was swallowed during active sessions.
- **Fix:** Moved command detection before active session check.
- **Lesson:** Commands are the user's escape hatch — always check them first in intent routing.

## 2026-04-01: Playwright tests outdated — intel page UI refactored from Feed to Chat

- **Category:** knowledge_gap
- **Area:** tests
- **Context:** `tests/test_06_intel.py` asserts existence of "情報 Feed" heading, `.rounded-xl` cards with "已確認|草稿" badges — all remnants of the old list UI. Current UI is a chat-style interface (sidebar + conversation). All 6 intel tests fail.
- **Lesson:** When the intel page UI was refactored (Sprint ~S37+), the Playwright tests were not updated. Before running QA, check if test assertions match the current UI shape.
- **Action needed:** Rewrite `tests/test_06_intel.py` to match the chat-style UI: sidebar list, conversation area, input box with Mic button, "情報紀錄" heading.

## 2026-04-01: Playwright tests all fail when Docker DB is not running

- **Category:** best_practice
- **Area:** tests
- **Context:** All Playwright tests (test_02 through test_10) fail when Docker (`spms-postgres`) is not started — backend returns 500 on every data endpoint, causing pages to crash or show empty state.
- **Lesson:** Before running `pytest`, always ensure Docker is up: `docker start spms-postgres`. Add a preflight check to `conftest.py` or `run_qa.sh`.

## 2026-03-26: DB schema vs live DB divergence (nx_meeting.deal_id)
- **Category:** bug_discovery
- **Context:** `schema.sql` had `deal_id INTEGER REFERENCES nx_deal(id)` (nullable) but live DB had NOT NULL.
- **Fix:** `ALTER TABLE nx_meeting ALTER COLUMN deal_id DROP NOT NULL`
- **Lesson:** Always verify live DB constraints match schema.sql — they can diverge from manual changes.
