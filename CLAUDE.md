# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SPMS (Sales & Project Management System) — B2B 業務與專案管理系統。Tech stack: **Python + Streamlit + PostgreSQL** (psycopg2, no ORM). Designed for solo + AI-assisted development.

## Development Commands

```bash
# Start PostgreSQL
docker-compose up -d

# Initialize database (creates all 11 tables)
python -c "from database.connection import init_db; init_db()"

# Run S09 migration (if upgrading from S08)
python database/migrate_s09.py

# Run CRM retro migration (champion→champions, DM structure)
python database/migrate_crm_retro.py

# Run S10 migration (contact normalization)
python database/migrate_s10.py

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
- **JSONB fields** in `crm` table (`decision_maker`, `champions`) — use `psycopg2.extras.Json()` for writes.
- **State machine** in `services/project.py` — `transition_status()` enforces `VALID_TRANSITIONS` from `constants.py`. Illegal transitions raise `ValueError`.
- **`constants.py`** is the single source of truth for status codes (L0–L7, P0–P2, LOST, HOLD), action types, task statuses, inactive statuses, and valid transitions.
- **`app_settings` table** stores customizable page headers; `components/sidebar.py` reads them dynamically.
- **Presale/postsale separation** — `presale_owner`, `sales_owner`, and `postsale_owner` are separate fields in `project_list`. Pages `presale.py` and `postsale.py` filter by status code prefix.
- **Grouped sidebar navigation** — `components/sidebar.py` uses `_NAV_SECTIONS` to render pages in sections (年度戰略, 售前管理, 售後管理, 客戶關係管理) with bold headers and indented sub-pages.

### Database: 11 Tables

Core (Phase 1-2): `annual_plan`, `crm`, `project_list`, `sales_plan`, `work_log`, `project_task`, `app_settings`, `contact`, `account_contact`
Reserved (Phase 3): `email_log`, `agent_actions`

`project_list` is the central hub — FK references from `work_log`, `sales_plan`, `project_task`, `email_log`, `agent_actions`.

`project_task` stores sub-tasks for postsale projects (statuses: planned/in_progress/completed). Used by `postsale_detail.py` for task CRUD, Gantt chart, and burndown chart.

`contact` + `account_contact` normalize CRM contact data (S10). `services/crm.py` dual-writes to both JSONB fields and normalized tables. JSONB fields retained for backward compatibility until S11+ confirms stability.

### State Machine (Status Codes)

Pre-sale: L0 客戶開發 → L1 等待追蹤 → L2 提案 → L3 確認意願 → L4 執行POC → L5 完成POC → L6 議價 → L7 簽約

Post-sale: P0 規劃 → P1 執行 → P2 驗收

All L0-L6 stages can transition to LOST or HOLD. L7 is pre-sale terminal (transitions to P0 post-sale). Inactive statuses (L7, P2, LOST, HOLD) are filtered from work log project selectors.

## Sprint Methodology

5-stage workflow per Sprint: **Kickoff → Planning → Vibe Coding → Review → Retro & Refactor**

- Sprint files: `docs/sprints/S01.md` through `S09.md`
- Sprint guide: `docs/SPRINT_GUIDE.md`
- Full dev plan: `docs/DEVELOPMENT_PLAN.md`

S03 and S04 can run in parallel (both depend only on S02). S10-S13 為 Phase 2 進行中。

Every Sprint **Kickoff** (Stage 0) and **Retro & Refactor** (Stage 4) must automatically commit and push to GitHub. This ensures progress checkpoints are always synced to the remote repository.

## Language

All documentation and UI text is in **Traditional Chinese (繁體中文)**. Code identifiers and comments are in English.
