Clean up build artifacts, caches, and stale files from the project.

Steps:

1. Find and delete Python cache directories:
   ```
   find . -type d -name __pycache__ -not -path './node_modules/*' -not -path './frontend/node_modules/*'
   ```
   Show the list, then delete each with `rm -r`.

2. Check for misplaced `.next/` at project root (should only be in `frontend/.next/`):
   - If found at root, delete with `rm -r .next/`

3. Check for `test-results/` and `frontend/test-results/`:
   - If found, delete with `rm -r`

4. Check for `.pytest_cache/` directories:
   - If found, delete with `rm -r`

5. Verify `.gitignore` includes these patterns:
   - `__pycache__/`
   - `.next/`
   - `test-results/`
   - `*.db`
   - `.env`
   - `node_modules/`

6. Report what was cleaned:

| Item | Action |
|------|--------|
| `__pycache__/` (N dirs) | Deleted |
| `.next/` (root) | Deleted / Not found |
| `test-results/` | Deleted / Not found |
| `.gitignore` | OK / Missing entries: ... |

Do NOT delete `frontend/.next/` — that's the active build cache.
Do NOT delete `node_modules/` — use `npm ci` to rebuild if needed.
