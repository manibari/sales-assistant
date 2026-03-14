# .claude/CLAUDE.md

Claude Code specific instructions for this repository. For universal project specs, see:

@AGENTS.md

## Sprint Methodology

5-stage workflow per Sprint: **Kickoff → Planning → Vibe Coding → Review → Retro & Refactor**

- Sprint files: `docs/sprints/S01.md` through current
- Sprint guide: `docs/SPRINT_GUIDE.md`
- Full dev plan: `docs/DEVELOPMENT_PLAN.md`

Phase 1-2 (S01–S16): SPMS foundation, completed.
Phase 3 (S17–S32): AI & stability, completed.
Phase 4 (S33+): Project Nexus — Next.js + FastAPI full-stack, relationship graph, voice input.

## Sprint Auto-Behaviors

Every Sprint **Kickoff** (Stage 0) and **Retro & Refactor** (Stage 4) must automatically commit and push to GitHub.

## Sprint Retro Codebase Validation

After every Sprint **Retro** completes, re-read `docs/DEVELOPMENT_PLAN.md` and compare against actual codebase. Alert on discrepancies before proceeding.

## Phase 4 Context

- **Next.js** is the primary frontend (React 19 + TypeScript + Tailwind CSS)
- **FastAPI** wraps existing `services/*.py` as REST API
- **Streamlit** removed — archived to `_archive/streamlit/`
- **D3.js / react-force-graph** for relationship network visualization
- New tables: `stakeholder_relation`, `intel`, `intel_org`
- iPhone dictation for voice input (Whisper deferred)

## Frontend Development Rules

- Always design UI/UX before coding (wireframe → component tree → implementation)
- Use `frontend-design` and `ui-ux-pro-max` skills for design phase
- Use `plan-check-style` when entering plan mode for frontend tasks
- TypeScript strict mode, Tailwind CSS, Server Components by default
