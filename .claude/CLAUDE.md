# .claude/CLAUDE.md

Claude Code specific instructions for this repository. For universal project specs, see:

@AGENTS.md

## Sprint Methodology

5-stage workflow per Sprint: **Kickoff → Planning → Vibe Coding → Review → Retro & Refactor**

- Sprint files: `docs/sprints/S01.md` through `S32.md`
- Sprint guide: `docs/SPRINT_GUIDE.md`
- Full dev plan: `docs/DEVELOPMENT_PLAN.md`

S03 and S04 can run in parallel (both depend only on S02). S07-S13 為 Phase 2（已完成）。S14-S16 為客戶回饋改進（S14→S15→S16 依賴鏈）。

## Sprint Auto-Behaviors

Every Sprint **Kickoff** (Stage 0) and **Retro & Refactor** (Stage 4) must automatically commit and push to GitHub. This ensures progress checkpoints are always synced to the remote repository.

## Sprint Retro Codebase Validation

After every Sprint **Retro** completes, re-read `docs/DEVELOPMENT_PLAN.md` and compare it against the actual codebase (schema, services, pages, directory structure). If any discrepancies are found (e.g., table count, column names, page list, directory tree, sprint table), alert the developer before proceeding to the next Sprint.
