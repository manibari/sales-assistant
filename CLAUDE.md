# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SPMS (Sales & Project Management System) — B2B 業務與專案管理系統。Tech stack: **Python + Streamlit + PostgreSQL** (psycopg2, no ORM). Designed for solo + AI-assisted development.

## Development Commands

```bash
# Start PostgreSQL
docker-compose up -d

# Initialize database (creates all 13 tables)
python -c "from database.connection import init_db; init_db()"

# Run S09 migration (if upgrading from S08)
python database/migrate_s09.py

# Run CRM retro migration (champion→champions, DM structure)
python database/migrate_crm_retro.py

# Run S10 migration (contact normalization)
python database/migrate_s10.py

# Run S11 migration (stage_probability + project_contact)
python database/migrate_s11.py

# Run S12 migration (due_date + is_next_action)
python database/migrate_s12.py

# Run S14 migration (client-level activities: nullable project_id + client_id FK)
python database/migrate_s14.py

# Run S15 migration (JSONB vs normalized validation report)
python database/migrate_s15.py

# Run S16 migration (contact dedup + UNIQUE INDEX)
python database/migrate_s16.py

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
- **JSONB fields** in `crm` table (`decision_maker`, `champions`) — legacy columns retained for reference. S15 retired dual-write; all reads/writes now use normalized `contact` + `account_contact` tables only.
- **State machine** in `services/project.py` — `transition_status()` enforces `VALID_TRANSITIONS` from `constants.py`. Illegal transitions raise `ValueError`.
- **`constants.py`** is the single source of truth for status codes (L0–L7, P0–P2, LOST, HOLD), action types, task statuses, inactive statuses, valid transitions, and health score weights/thresholds.
- **`app_settings` table** stores customizable page headers; `components/sidebar.py` reads them dynamically.
- **Presale/postsale separation** — `presale_owner`, `sales_owner`, and `postsale_owner` are separate fields in `project_list`. Pages `presale.py` and `postsale.py` filter by status code prefix.
- **Grouped sidebar navigation** — `components/sidebar.py` uses `_NAV_SECTIONS` to render pages in sections (年度戰略, 售前管理, 售後管理, 客戶關係管理) with bold headers and indented sub-pages. 售前管理含售前看板（kanban.py），全域搜尋為 standalone 頁面。
- **Stage probability** — `stage_probability` table stores per-status default win probabilities. `services/stage_probability.py` provides CRUD. Used for sales plan prefill and pipeline weighted forecast.
- **Project-contact linking** — `project_contact` table (many-to-many). `services/project.py` provides link_contact / unlink_contact / get_contacts. Used by `presale_detail.py`.
- **Client-level activities (S14)** — `work_log.project_id` is nullable; `work_log.client_id` FK to `crm`. CHECK constraint ensures at least one is set. `pages/work_log.py` has radio toggle for project vs client activity mode.
- **Client health score (S16)** — `services/client_health.py` computes 0-100 score (activity recency + frequency + deal value + deal progress). Displayed in CRM overview and detail pages. Thresholds in `constants.py`.
- **Contact dedup (S16)** — `contact` table has UNIQUE INDEX on `(name, COALESCE(email, ''))`. `services/contact.py` uses INSERT ON CONFLICT (upsert).

### Database: 13 Tables

Core (Phase 1-2): `annual_plan`, `crm`, `project_list`, `sales_plan`, `work_log`, `project_task`, `app_settings`, `contact`, `account_contact`, `stage_probability`, `project_contact`
Reserved (Phase 3): `email_log`, `agent_actions`

`project_list` is the central hub — FK references from `work_log`, `sales_plan`, `project_task`, `project_contact`, `email_log`, `agent_actions`.

`project_task` stores sub-tasks for presale/postsale projects (statuses: planned/in_progress/completed, + `due_date` + `is_next_action`). Used by `presale_detail.py` and `postsale_detail.py` for task CRUD, Gantt chart, and burndown chart.

`contact` + `account_contact` normalize CRM contact data (S10). Since S15, `services/crm.py` writes only to normalized tables (JSONB dual-write retired). `contact` has a UNIQUE INDEX on `(name, COALESCE(email, ''))` since S16.

`stage_probability` stores per-stage default probabilities (L0=5%...L7=100%). Used by `sales_plan.py` for confidence prefill and `pipeline.py` for weighted revenue forecast. Editable via `settings.py`.

`project_contact` links contacts to projects (many-to-many). Used by `presale_detail.py` for managing deal-level stakeholders.

### State Machine (Status Codes)

Pre-sale: L0 客戶開發 → L1 等待追蹤 → L2 提案 → L3 確認意願 → L4 執行POC → L5 完成POC → L6 議價 → L7 簽約

Post-sale: P0 規劃 → P1 執行 → P2 驗收

All L0-L6 stages can transition to LOST or HOLD. L7 is pre-sale terminal (transitions to P0 post-sale). Inactive statuses (L7, P2, LOST, HOLD) are filtered from work log project selectors.

## Sprint Methodology

5-stage workflow per Sprint: **Kickoff → Planning → Vibe Coding → Review → Retro & Refactor**

- Sprint files: `docs/sprints/S01.md` through `S16.md`
- Sprint guide: `docs/SPRINT_GUIDE.md`
- Full dev plan: `docs/DEVELOPMENT_PLAN.md`

S03 and S04 can run in parallel (both depend only on S02). S07-S13 為 Phase 2（已完成）。S14-S16 為客戶回饋改進（S14→S15→S16 依賴鏈）。

Every Sprint **Kickoff** (Stage 0) and **Retro & Refactor** (Stage 4) must automatically commit and push to GitHub. This ensures progress checkpoints are always synced to the remote repository.

After every Sprint **Retro** completes, re-read `docs/DEVELOPMENT_PLAN.md` and compare it against the actual codebase (schema, services, pages, directory structure). If any discrepancies are found (e.g., table count, column names, page list, directory tree, sprint table), alert the developer before proceeding to the next Sprint.

## Language

All documentation and UI text is in **Traditional Chinese (繁體中文)**. Code identifiers and comments are in English.
