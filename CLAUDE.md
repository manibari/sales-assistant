# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SPMS (Sales & Project Management System) — B2B 業務與專案管理系統。Tech stack: **Python + Streamlit + PostgreSQL** (psycopg2, no ORM). Designed for solo + AI-assisted development.

## Development Commands

```bash
# Start PostgreSQL
docker-compose up -d

# Initialize database (creates all 8 tables)
python -c "from database.connection import init_db; init_db()"

# Load seed data
python database/seed.py

# Run the app
streamlit run app.py
```

No test framework is set up yet. Validation is manual per Sprint DoD checklists.

## Architecture

### Data Flow

```
Streamlit Pages (pages/*.py)
    → Services (services/*.py) — raw SQL CRUD, no ORM
    → Connection Pool (database/connection.py) — psycopg2.pool
    → PostgreSQL (docker-compose.yml)
```

### Key Architectural Decisions

- **psycopg2 + raw SQL** — no ORM, no SQLAlchemy. PostgreSQL is the final target, no abstraction needed.
- **JSONB fields** in `crm` table (`decision_maker`, `champion`) — use `psycopg2.extras.Json()` for writes.
- **State machine** in `services/project.py` — `transition_status()` enforces `VALID_TRANSITIONS` from `constants.py`. Illegal transitions raise `ValueError`.
- **`constants.py`** is the single source of truth for status codes (S01–D03, LOST, HOLD), action types, inactive statuses, and valid transitions.
- **`app_settings` table** stores customizable page headers; `components/sidebar.py` reads them dynamically.

### Database: 8 Tables

Core (Phase 1): `annual_plan`, `crm`, `project_list`, `sales_plan`, `work_log`, `app_settings`
Reserved (Phase 3): `email_log`, `agent_actions`

`project_list` is the central hub — FK references from `work_log`, `sales_plan`, `email_log`, `agent_actions`.

### State Machine (Status Codes)

S (Sales): S01→S02→S03→S04 | T (Tech): T01→T02 | C (Closing): C01→C02→C03→C04 | D (Delivery): D01→D02→D03

All S/T/C stages can transition to LOST or HOLD. D series cannot go backward. Inactive statuses (D03, LOST, HOLD) are filtered from work log project selectors.

## Sprint Methodology

5-stage workflow per Sprint: **Kickoff → Planning → Vibe Coding → Review → Retro & Refactor**

- Sprint files: `docs/sprints/S01.md` through `S06.md`
- Sprint guide: `docs/SPRINT_GUIDE.md`
- Full dev plan: `docs/DEVELOPMENT_PLAN.md`

S03 and S04 can run in parallel (both depend only on S02).

## Language

All documentation and UI text is in **Traditional Chinese (繁體中文)**. Code identifiers and comments are in English.
