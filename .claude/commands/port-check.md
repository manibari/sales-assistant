Scan codebase for hardcoded port numbers and verify consistency with AGENTS.md Network Config.

Steps:

1. Read AGENTS.md and extract the Network Config table (canonical ports).
2. Search all `*.py`, `*.ts`, `*.tsx`, `*.sh`, `*.md`, `*.yml`, `*.json` files for port references:
   - Pattern: `:3000`, `:3333`, `:8000`, `:8001`, `:5432`, `:6543`
   - Exclude: `node_modules/`, `.next/`, `__pycache__/`, `package-lock.json`
3. For each match, classify:
   - ✅ Consistent with Network Config
   - ⚠️ Inconsistent (e.g., `:8000` where it should be `:8001`)
   - ℹ️ Not a port reference (e.g., `[:8000]` as string truncation limit)
4. Report a summary table:

| File | Line | Found | Expected | Status |
|------|------|-------|----------|--------|
| ... | ... | :8000 | :8001 | ⚠️ |

5. If inconsistencies found, ask user whether to fix them.

Do NOT auto-fix. Only report.
