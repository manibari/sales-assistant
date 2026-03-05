# .claude/CLAUDE.md

Claude Code specific instructions for this repository. For universal project specs, see:

@AGENTS.md

## Sprint Methodology

5-stage workflow per Sprint: **Kickoff → Planning → Vibe Coding → Review → Retro & Refactor**

- Sprint files: `docs/sprints/S01.md` through `S32.md`
- Sprint guide: `docs/SPRINT_GUIDE.md`
- Full dev plan: `docs/DEVELOPMENT_PLAN.md`

Phase 1-2 (S01–S16): SPMS foundation, completed.
Phase 3 (S17–S32): AI & stability, completed.
Phase 4 (S33+): Project Nexus — relationship graph, FastAPI webhook, voice input, Notion sync.

## Sprint Auto-Behaviors

Every Sprint **Kickoff** (Stage 0) and **Retro & Refactor** (Stage 4) must automatically commit and push to GitHub. This ensures progress checkpoints are always synced to the remote repository.

## Sprint Retro Codebase Validation

After every Sprint **Retro** completes, re-read `docs/DEVELOPMENT_PLAN.md` and compare it against the actual codebase (schema, services, pages, directory structure). If any discrepancies are found (e.g., table count, column names, page list, directory tree, sprint table), alert the developer before proceeding to the next Sprint.

## Phase 4 Context

Project Nexus integrates on top of existing SPMS. Key principles:
- PostgreSQL remains the single source of truth
- FastAPI is a thin webhook layer, not a replacement for Streamlit
- New tables (`stakeholder_relation`, `intel`, `intel_org`) extend the existing `contact` and `crm` models
- pyvis/networkx for relationship graph visualization
- Notion is read-only sync target, never a write source
