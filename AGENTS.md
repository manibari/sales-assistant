# AGENTS.md

Universal project specs for all AI-assisted tools (Claude Code, Cursor, Copilot, etc.).

## Project Overview

**Project Nexus（太陽型戰略控制台）** — 以「人」為核心、「AI 語音」驅動輸入、「資訊槓桿」為輸出導向的 B2B 個人戰略大腦。

建立在既有 SPMS（Sales & Project Management System）之上，擴展為全端架構：Next.js 前端 + FastAPI 後端 + PostgreSQL。

### Tech Stack

**Frontend**: Next.js (React 19) + TypeScript + Tailwind CSS + D3.js/react-force-graph (relationship network)
**Backend**: FastAPI (Python) — REST API wrapping existing services layer
**Database**: Supabase PostgreSQL (psycopg2 + connection pool, no ORM)
**AI**: Gemini / Azure OpenAI / Anthropic (multi-provider, existing)
**Voice Input**: iPhone built-in dictation → text (Whisper deferred)

### Success Metrics

- **輸入極簡化**: 語音/截圖輸入至結構化入庫 < 15 秒
- **情報關聯率**: 每筆新情報自動映射至少一個 Stakeholder

## Architecture

```
A. 輸入層 (Capture)          B. 處理層 (Backend)          C. 呈現層 (Frontend)
┌──────────────────┐      ┌──────────────────────┐      ┌──────────────────────┐
│ iOS Shortcuts    │      │ FastAPI              │      │ Next.js              │
│ iPhone 語音轉文字 │─────→│   /api/ingest        │─────→│   關係網絡圖 (D3.js) │
│ Mac 右鍵捷徑     │      │   /api/crm/*         │      │   戰略看板           │
│ Next.js 前端     │      │   /api/projects/*    │      │   Pipeline 漏斗      │
│ (Streamlit 內部) │      │   /api/network/*     │      │   MEDDIC 面板        │
└──────────────────┘      │ worker.py (async AI) │      │   Mobile PWA         │
                          │ services/*.py (CRUD) │      └──────────────────────┘
                          │ PostgreSQL (SSOT)    │
                          └──────────────────────┘      Streamlit (internal admin)
```

- **PostgreSQL 是單一事實來源**
- **FastAPI** 同時服務 Next.js 前端 + 外部 webhook（iOS Shortcuts via Make.com）
- **Streamlit** 已退役（archived）

## Network Config

All ports are defined here. Do NOT hardcode port numbers elsewhere — reference this section.

| Service | Port | URL | Notes |
|---------|------|-----|-------|
| Next.js frontend | 3000 | `http://localhost:3000` | Dev server |
| FastAPI backend | **8001** | `http://localhost:8001` | `next.config.ts` rewrites `/api/*` here |
| Supabase PostgreSQL | 5432 | via `DATABASE_URL` in `.env` | Remote, no local DB |
| Production frontend | 443 | `https://sales.phyra.uk` | Deployed |
| Production backend | 443 | `https://api.phyra.uk` | Deployed |
| Telegram webhook | — | `https://api.phyra.uk/api/nx/telegram/webhook` | Set via Telegram API |

**Key rule**: Frontend proxies API calls via `next.config.ts` rewrite → `http://127.0.0.1:8001`. Backend CORS also allows direct access from `:3000` and `:3333`.

## Build & Run

```bash
# --- Database (Supabase, remote) ---
# Set DATABASE_URL in .env (see .env.example)
python -c "from database.connection import init_db; init_db()"

# --- Backend (FastAPI) ---
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8001

# --- Frontend (Next.js) ---
cd frontend
npm install
npm run dev    # http://localhost:3000

# --- Quick start (both servers) ---
./scripts/start.sh

# --- Async AI Worker ---
python worker.py
```

## Project Structure

```
sales-assistant/
├── frontend/                # Next.js app (Phase 4)
│   ├── src/
│   │   ├── app/             # App Router pages
│   │   ├── components/      # React components
│   │   └── lib/             # API client, utils
│   ├── package.json
│   ├── tailwind.config.ts
│   └── tsconfig.json
├── backend/                 # FastAPI app (Phase 4)
│   ├── main.py              # FastAPI entry + CORS
│   ├── routers/             # API route modules
│   └── requirements.txt     # FastAPI + uvicorn
├── services/                # Business logic (shared by FastAPI + Streamlit + worker)
├── database/                # Schema, migrations, connection pool
├── pages/                   # Streamlit pages (legacy admin)
├── components/              # Streamlit components (legacy)
├── app.py                   # Streamlit entry (legacy admin)
├── worker.py                # Async AI task worker
├── constants.py             # Status codes, transitions, weights
├── prompts.yml              # AI prompt templates
├── rules.yml                # MEDDIC gate rules
└── docs/                    # Sprint docs, dev plan
```

## Coding Style

### Python (Backend + Services)
- Functional patterns, early returns
- Type hints on all function signatures
- Raw SQL via psycopg2, no ORM
- Internal `_create(cur)` pattern for nested transactions

### TypeScript (Frontend)
- React functional components with hooks
- TypeScript strict mode
- Tailwind CSS for styling, no CSS modules
- Server Components by default, Client Components only when needed (interactivity)
- API calls via a centralized `lib/api.ts` client

### General
- No over-engineering — minimum complexity for current requirements
- No premature abstractions
- Comments only where logic isn't self-evident

## Architecture Decisions

- **psycopg2 + raw SQL** — no ORM, no SQLAlchemy. PostgreSQL is the final target.
- **Services layer shared** — `services/*.py` is consumed by FastAPI routers, Streamlit pages, and worker.py. This is the single business logic layer.
- **State machine** in `services/project.py` — `transition_status()` enforces `VALID_TRANSITIONS` from `constants.py`.
- **`constants.py`** — single source of truth for status codes, transitions, action types, health weights.
- **MEDDIC stage gating (S25)** — `project_meddic` + `rules.yml` gate rules before status transitions.
- **Async AI processing (S29)** — `ai_task_queue` + `worker.py` poll loop, supports batch entries.
- **Cursor-to-dict helpers** — `database/connection.py` provides `row_to_dict(cur)` / `rows_to_dicts(cur)`.
- **Centralized config** — `services/config.py` uses `@lru_cache` for `rules.yml` and `prompts.yml`.
- **Contact dedup** — UNIQUE INDEX on `(name, COALESCE(email, ''))`, upsert via ON CONFLICT.
- **Stakeholder relationship graph (Phase 4)** — `stakeholder_relation` + `intel` + `intel_org` tables model cross-org influence. Visualized via D3.js/react-force-graph in Next.js.
- **FastAPI as API gateway (Phase 4)** — wraps existing services, serves Next.js frontend + iOS webhook intake.

## Database Schema

### Core Tables (Phase 1-2, S01–S16): 11 tables

`annual_plan`, `crm`, `project_list`, `sales_plan`, `work_log`, `project_task`, `app_settings`, `contact`, `account_contact`, `stage_probability`, `project_contact`

### Feature Tables (S25/S29): 2 tables

`project_meddic`, `ai_task_queue`

### Phase 4 — Nexus Tables (planned): 3 tables

```sql
stakeholder_relation (
    id SERIAL PRIMARY KEY,
    from_contact_id INTEGER REFERENCES contact(contact_id),
    to_contact_id   INTEGER REFERENCES contact(contact_id),
    relation_type   TEXT NOT NULL,  -- 'referral', 'reports_to', 'influences', 'competitor_of'
    notes           TEXT,
    leverage_value  TEXT DEFAULT 'medium',  -- 'high', 'medium', 'low'
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

intel (
    id SERIAL PRIMARY KEY,
    title             TEXT NOT NULL,
    summary           TEXT,
    leverage_value    TEXT DEFAULT 'medium',
    source_contact_id INTEGER REFERENCES contact(contact_id),
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

intel_org (
    intel_id INTEGER REFERENCES intel(id) ON DELETE CASCADE,
    crm_id   TEXT REFERENCES crm(client_id) ON DELETE CASCADE,
    PRIMARY KEY (intel_id, crm_id)
);
```

### Reserved Tables: 2 tables

`email_log`, `agent_actions`

### Key Relationships

`project_list` — central hub (FK from work_log, sales_plan, project_task, project_contact, project_meddic).
`contact` — people hub (FK from account_contact, project_contact, stakeholder_relation, intel).

## State Machine (Status Codes)

Pre-sale: L0 → L1 → L2 → L3 → L4 → L5 → L6 → L7
Post-sale: P0 → P1 → P2
All L0-L6 can transition to LOST or HOLD. L7 → P0. Inactive: L7, P2, LOST, HOLD.

## Development Phases

### Phase 1-2 (S01–S16): SPMS Foundation — COMPLETED
Core CRM, presale/postsale pipeline, work log, contacts, health scores.

### Phase 3 (S17–S32): AI & Stability — COMPLETED
AI smart log, MEDDIC gating, async worker, batch parsing, connection fixes.

### Phase 4 (S33+): Project Nexus — IN PROGRESS
1. **S33**: Full-stack scaffolding — FastAPI backend + Next.js frontend + Nexus DB tables
2. **S34+**: Relationship network graph (D3.js), CRM/pipeline frontend, webhook intake, Notion sync

## Language

All documentation and UI text in **Traditional Chinese**. Code identifiers and comments in English.
