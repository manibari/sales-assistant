# AGENTS.md

Universal project specs for all AI-assisted tools (Claude Code, Cursor, Copilot, etc.).

## Project Overview

**Project Nexus（太陽型戰略控制台）** — 以「人」為核心、「AI 語音」驅動輸入、「資訊槓桿」為輸出導向的 B2B 個人戰略大腦。

建立在既有 SPMS（Sales & Project Management System）之上，擴展為三層架構：移動端語音/截圖輸入 → 雲端 AI 處理 → PostgreSQL + Streamlit 管理後台 + 關係網絡圖。

Tech stack: **Python + Streamlit + FastAPI + PostgreSQL** (psycopg2, no ORM) + **pyvis/networkx**（關係網絡圖）。設計為 solo + AI-assisted development。

### Success Metrics

- **輸入極簡化**: 語音/截圖輸入至結構化入庫 < 15 秒
- **情報關聯率**: 每筆新情報自動映射至少一個 Stakeholder

## Architecture (IPO)

```
A. 輸入層 (Capture)          B. 處理層 (AI Logic)         C. 儲存與戰略層 (Board)
┌──────────────────┐      ┌──────────────────────┐      ┌──────────────────────┐
│ iOS Shortcuts    │      │ Make.com / n8n       │      │ PostgreSQL (SSOT)    │
│ Mac 右鍵捷徑     │─────→│ Whisper API (STT)    │─────→│ FastAPI 薄 API 層    │
│ Streamlit 文字框 │      │ GPT-4o / Claude      │      │ Streamlit 管理後台   │
│ (既有 AI 記錄)   │      │ (結構化擷取)          │      │ pyvis 關係網絡圖     │
└──────────────────┘      └──────────────────────┘      │ Notion 戰略看板(同步)│
                                                        └──────────────────────┘
```

- **PostgreSQL 是單一事實來源**，Notion 僅做單向同步的戰略視覺化看板
- **FastAPI** 暴露 webhook 端點供 Make.com 呼叫，資料流入既有 services 層

## Build & Run

```bash
# Start PostgreSQL
docker-compose up -d

# Initialize database (creates all tables)
python -c "from database.connection import init_db; init_db()"

# Run migrations (in order if upgrading)
python database/migrate_s09.py
python database/migrate_crm_retro.py
python database/migrate_s10.py
python database/migrate_s11.py
python database/migrate_s12.py
python database/migrate_s14.py
python database/migrate_s15.py
python database/migrate_s16.py

# Import 48 presale projects (products + clients + projects + work_log)
python database/import_projects.py

# Load seed data
python database/seed.py

# Run the Streamlit app
streamlit run app.py

# Run the async AI worker
python worker.py

# Run the FastAPI webhook server (Phase 4)
# uvicorn api:app --port 8000
```

No test framework is set up yet. Validation is manual per Sprint DoD checklists.

## Project Structure

### Data Flow

```
iOS Shortcuts / 語音
    → Make.com (Whisper STT)
    → FastAPI webhook (/api/ingest)
    → ai_task_queue (PostgreSQL)
    → worker.py (poll loop)
    → Services (services/*.py) — raw SQL CRUD
    → Connection Pool (database/connection.py) — psycopg2.pool
    → PostgreSQL

Streamlit Pages (pages/*.py)
    → Services (services/*.py)
    → PostgreSQL

pyvis 關係網絡圖 (pages/network.py)
    → services/network.py (graph queries)
    → PostgreSQL (contact, stakeholder_relation, intel)
```

## Architecture Decisions

- **psycopg2 + raw SQL** — no ORM, no SQLAlchemy. PostgreSQL is the final target, no abstraction needed.
- **JSONB fields** in `crm` table (`decision_maker`, `champions`) — legacy columns retained for reference. S15 retired dual-write; all reads/writes now use normalized `contact` + `account_contact` tables only.
- **State machine** in `services/project.py` — `transition_status()` enforces `VALID_TRANSITIONS` from `constants.py`. Illegal transitions raise `ValueError`.
- **`constants.py`** is the single source of truth for status codes (L0–L7, P0–P2, LOST, HOLD), action types, task statuses, inactive statuses, valid transitions, and health score weights/thresholds.
- **`app_settings` table** stores customizable page headers; `components/sidebar.py` reads them dynamically.
- **Presale/postsale separation** — `presale_owner`, `sales_owner`, `postsale_owner`, and `channel` are separate fields in `project_list`. Pages `presale.py` and `postsale.py` filter by status code prefix.
- **Grouped sidebar navigation** — `components/sidebar.py` uses `_NAV_SECTIONS` to render pages in sections with bold headers and indented sub-pages.
- **Stage probability** — `stage_probability` table stores per-status default win probabilities. Used for sales plan prefill and pipeline weighted forecast.
- **Project-contact linking** — `project_contact` table (many-to-many). Used by `presale_detail.py`.
- **Client-level activities (S14)** — `work_log.project_id` is nullable; `work_log.client_id` FK to `crm`. CHECK constraint ensures at least one is set.
- **Client health score (S16)** — `services/client_health.py` computes 0-100 score. Thresholds in `constants.py`.
- **Contact dedup (S16)** — `contact` table has UNIQUE INDEX on `(name, COALESCE(email, ''))`. Uses INSERT ON CONFLICT (upsert).
- **MEDDIC stage gating (S25)** — `project_meddic` table stores per-project MEDDIC data. `services/project.py` checks `rules.yml` gate rules before allowing status transitions; `force=True` bypasses.
- **Async AI processing (S29)** — `ai_task_queue` table + `worker.py` poll loop. Supports batch entries (multiple parsed results per task).
- **Cursor-to-dict helpers** — `database/connection.py` provides `row_to_dict(cur)` / `rows_to_dicts(cur)` used by all services.
- **Centralized config loading** — `services/config.py` uses `@lru_cache` for `rules.yml` and `prompts.yml`.
- **Stakeholder relationship graph (Phase 4)** — `stakeholder_relation` + `intel` + `intel_org` tables model cross-org influence and intelligence leverage. Visualized via pyvis in `pages/network.py`.
- **FastAPI webhook layer (Phase 4)** — thin API for external intake (voice/screenshot from iOS Shortcuts via Make.com), feeds into existing `ai_task_queue` + worker pipeline.

## Database Schema

### Core Tables (Phase 1-2, S01–S16): 11 tables

`annual_plan`, `crm`, `project_list`, `sales_plan`, `work_log`, `project_task`, `app_settings`, `contact`, `account_contact`, `stage_probability`, `project_contact`

### Feature Tables (S25/S29): 2 tables

`project_meddic`, `ai_task_queue`

### Phase 4 — Nexus Tables (planned): 3 tables

```sql
-- Stakeholder cross-org influence
stakeholder_relation (
    id SERIAL PRIMARY KEY,
    from_contact_id INTEGER REFERENCES contact(contact_id),
    to_contact_id   INTEGER REFERENCES contact(contact_id),
    relation_type   TEXT NOT NULL,  -- 'referral', 'reports_to', 'influences', 'competitor_of'
    notes           TEXT,
    leverage_value  TEXT DEFAULT 'medium',  -- 'high', 'medium', 'low'
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Intelligence / leverage items
intel (
    id SERIAL PRIMARY KEY,
    title             TEXT NOT NULL,
    summary           TEXT,
    leverage_value    TEXT DEFAULT 'medium',
    source_contact_id INTEGER REFERENCES contact(contact_id),
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

-- Many-to-many: intel ↔ organizations
intel_org (
    intel_id INTEGER REFERENCES intel(id) ON DELETE CASCADE,
    crm_id   TEXT REFERENCES crm(client_id) ON DELETE CASCADE,
    PRIMARY KEY (intel_id, crm_id)
);
```

### Reserved Tables (Phase 3): 2 tables

`email_log`, `agent_actions`

### Key Relationships

`project_list` is the central hub — FK references from `work_log`, `sales_plan`, `project_task`, `project_contact`, `project_meddic`, `email_log`, `agent_actions`.

`contact` is the people hub — FK references from `account_contact`, `project_contact`, `stakeholder_relation` (both sides), `intel`.

## State Machine (Status Codes)

Pre-sale: L0 → L1 → L2 → L3 → L4 → L5 → L6 → L7
Post-sale: P0 → P1 → P2
All L0-L6 can transition to LOST or HOLD. L7 transitions to P0. Inactive statuses (L7, P2, LOST, HOLD) filtered from work log selectors.

## File Registry

### Services (services/*.py)

| File | Lines | Public API |
|------|-------|-----------|
| crm.py | 253 | `create`, `find_or_create_client`, `get_all`, `get_by_id`, `update`, `delete` |
| project.py | 241 | `create`, `find_or_create_project`, `get_all`, `get_by_id`, `get_presale`, `get_postsale`, `get_closed`, `update`, `delete`, `transition_status`, `link_contact`, `unlink_contact`, `get_contacts` |
| client_health.py | 141 | `compute_health_score`, `compute_all_scores` |
| project_task.py | 129 | `create`, `get_by_project`, `get_by_id`, `update`, `delete`, `get_summary`, `get_completed_by_date`, `get_upcoming` |
| task_queue.py | 100 | `create_task`, `get_next_pending`, `get_recent_tasks`, `update_task_status` |
| contact.py | 94 | `create`, `get_by_id`, `get_by_client`, `update`, `delete`, `link_to_client`, `unlink_from_client` |
| work_log.py | 88 | `create`, `get_by_project`, `get_recent`, `get_by_client`, `get_client_only` |
| annual_plan.py | 87 | `create`, `get_all`, `get_by_id`, `update`, `delete` |
| sales_plan.py | 79 | `create`, `get_all`, `get_by_id`, `update`, `delete`, `get_summary_by_client` |
| analytics.py | 76 | `get_manpower_by_initiative`, `get_potential_pipeline_by_initiative` |
| intelligent_log.py | 61 | `parse_log_entry` |
| search.py | 56 | `search_all` |
| meddic.py | 51 | `get_by_project`, `save_or_update` |
| stage_probability.py | 44 | `get_all`, `get_by_code`, `update` |
| config.py | 35 | `get_meddic_gate_rules`, `get_ai_prompt` |
| settings.py | 27 | `get_all_headers`, `update_header` |

### Pages (pages/*.py)

| File | Lines | Purpose |
|------|-------|---------|
| presale_detail.py | 409 | Presale deal detail: status transitions, MEDDIC, tasks, contacts, activity log |
| crm.py | 378 | Client management: CRUD + contacts + health score |
| postsale_detail.py | 302 | Postsale project detail: tasks, Gantt, Burndown |
| presale.py | 195 | Presale deal list |
| postsale.py | 185 | Postsale project list |
| work_log.py | 182 | Work log (home): AI smart log + manual mode + task queue |
| annual_plan.py | 181 | Product strategy: annual goals CRUD + war room |
| pipeline.py | 173 | Sales funnel: weighted revenue, stage distribution |
| sales_plan.py | 144 | Opportunity forecast: CRUD + stage probability prefill |
| post_closure.py | 89 | Closed deals: P2/LOST/HOLD overview |
| kanban.py | 86 | Presale kanban: columns by stage |
| settings.py | 80 | Settings: page headers, stage probability, cache clear |
| search.py | 61 | Global search: contacts/clients/projects |

### Infrastructure

| File | Lines | Purpose |
|------|-------|---------|
| database/import_projects.py | 280 | Import 4 products + 46 clients + 48 projects + work_log |
| database/schema.sql | 256 | 15+ table DDL + idempotent migrations |
| worker.py | 103 | Async AI task worker (polls ai_task_queue) |
| constants.py | 90 | Status codes, transitions, action types, health weights |
| database/connection.py | 81 | psycopg2 pool + `row_to_dict` / `rows_to_dicts` |
| components/sidebar.py | 69 | Grouped sidebar navigation |
| app.py | 28 | Streamlit entry: init_db → navigation → run |

## Development Phases

### Phase 1-2 (S01–S16): SPMS Foundation — COMPLETED
Core CRM, presale/postsale pipeline, work log, contacts, health scores.

### Phase 3 Iterative (S17–S32): AI & Stability — COMPLETED
AI smart log, MEDDIC gating, async worker, batch parsing, connection management fixes.

### Phase 4: Project Nexus — IN PROGRESS
1. **Batch AI parsing** — multi-entry AI log parsing with sales_owner/presale_owner/channel (uncommitted)
2. **Relationship network graph** — `stakeholder_relation` + `intel` tables, pyvis visualization in `pages/network.py`
3. **FastAPI webhook layer** — `/api/ingest` endpoint for voice/screenshot intake from iOS Shortcuts via Make.com
4. **Whisper integration** — `transcribe_audio()` in `intelligent_log.py`
5. **Notion sync** — one-way push from PostgreSQL strategic views to Notion boards
6. **Dynamic glossary** — entity resolution improvement with client/contact name dictionary in prompts

## Language

All documentation and UI text is in **Traditional Chinese**. Code identifiers and comments are in English.
