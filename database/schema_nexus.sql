-- Project Nexus Engine 1 — Complete Schema (SQLite)
-- Clean break from legacy SPMS tables. All tables prefixed nx_.

-- 1. Client organizations
CREATE TABLE IF NOT EXISTS nx_client (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    industry        TEXT,
    aliases         TEXT,          -- comma-separated alternate names
    budget_range    TEXT,          -- '<100K', '100-500K', '500K-1M', '1M+', 'unknown'
    status          TEXT NOT NULL DEFAULT 'active',  -- active, inactive
    notes           TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);

-- 2. Partner organizations
CREATE TABLE IF NOT EXISTS nx_partner (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    trust_level     TEXT NOT NULL DEFAULT 'unverified',  -- unverified, testing, verified, core_team, si_backed, demoted
    team_size       TEXT,          -- '1-10', '10-50', '50-200', '200+'
    aliases         TEXT,          -- comma-separated alternate names
    notes           TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);

-- 3. Contacts (people, linked to client OR partner)
CREATE TABLE IF NOT EXISTS nx_contact (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    title           TEXT,
    phone           TEXT,
    email           TEXT,
    line_id         TEXT,
    org_type        TEXT,          -- 'client', 'partner', 'si', 'other'
    org_id          INTEGER,       -- FK to nx_client.id or nx_partner.id (polymorphic)
    role            TEXT,          -- free text: decision maker, champion, engineer, etc.
    notes           TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_nx_contact_org ON nx_contact(org_type, org_id);

-- 4. Intelligence entries (raw + parsed)
CREATE TABLE IF NOT EXISTS nx_intel (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT,
    raw_input       TEXT NOT NULL,
    input_type      TEXT NOT NULL DEFAULT 'text',  -- 'text', 'photo', 'voice'
    parsed_json     TEXT,          -- AI-parsed structured output (JSON string)
    chat_history    TEXT,          -- JSON array of {role, text} chat messages
    status          TEXT NOT NULL DEFAULT 'draft',  -- draft, confirmed
    source_contact_id INTEGER REFERENCES nx_contact(id),
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);

-- 5. Universal tags
CREATE TABLE IF NOT EXISTS nx_tag (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    category        TEXT NOT NULL,  -- 'pain_point', 'capability', 'industry', 'solution'
    created_at      TEXT DEFAULT (datetime('now')),
    UNIQUE(name, category)
);

-- 6. Polymorphic tag join (entity_type + entity_id → any entity)
CREATE TABLE IF NOT EXISTS nx_entity_tag (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type     TEXT NOT NULL,  -- 'client', 'partner', 'intel', 'deal', 'contact'
    entity_id       INTEGER NOT NULL,
    tag_id          INTEGER NOT NULL REFERENCES nx_tag(id) ON DELETE CASCADE,
    created_at      TEXT DEFAULT (datetime('now')),
    UNIQUE(entity_type, entity_id, tag_id)
);
CREATE INDEX IF NOT EXISTS idx_nx_entity_tag_entity ON nx_entity_tag(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_nx_entity_tag_tag ON nx_entity_tag(tag_id);

-- 7. TBD items (skipped Q&A + meeting action items)
CREATE TABLE IF NOT EXISTS nx_tbd_item (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    question        TEXT NOT NULL,  -- the skipped question or action item
    context         TEXT,           -- additional context
    linked_type     TEXT,           -- 'client', 'partner', 'contact', 'deal'
    linked_id       INTEGER,
    source          TEXT NOT NULL DEFAULT 'skip',  -- 'skip' (Q&A), 'meeting', 'manual'
    resolved        INTEGER NOT NULL DEFAULT 0,   -- 0=open, 1=resolved
    resolved_at     TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_nx_tbd_linked ON nx_tbd_item(linked_type, linked_id, resolved);

-- 8. Document tracking (NDA/MOU)
CREATE TABLE IF NOT EXISTS nx_document (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id       INTEGER NOT NULL REFERENCES nx_client(id),
    doc_type        TEXT NOT NULL,  -- 'nda', 'mou'
    status          TEXT NOT NULL DEFAULT 'pending',  -- pending, in_progress, signed, not_required
    sign_date       TEXT,
    expiry_date     TEXT,
    file_path       TEXT,          -- path to uploaded file
    notes           TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_nx_document_client ON nx_document(client_id);

-- 9. Deals — the CORE entity
CREATE TABLE IF NOT EXISTS nx_deal (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    client_id       INTEGER NOT NULL REFERENCES nx_client(id),
    stage           TEXT NOT NULL DEFAULT 'L0',  -- L0, L1, L2, L3, L4, closed
    budget_range    TEXT,          -- legacy text: '<100K', '100-500K', etc. (kept for backward compat)
    budget_amount   REAL,          -- numeric budget in TWD (e.g. 300000 = 30萬)
    budget_year     INTEGER DEFAULT 2026,  -- fiscal year for this budget
    timeline        TEXT,          -- 'this_quarter', 'next_quarter', 'half_year', 'one_year', 'undecided'
    meddic_json     TEXT,          -- JSON: {metrics, economic_buyer, decision_criteria, decision_process, identify_pain, champion}
    close_reason    TEXT,          -- only set when stage='closed'
    close_notes     TEXT,
    status          TEXT NOT NULL DEFAULT 'active',  -- active, closed
    last_activity_at TEXT DEFAULT (datetime('now')),
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_nx_deal_client ON nx_deal(client_id);
CREATE INDEX IF NOT EXISTS idx_nx_deal_status ON nx_deal(status, stage);

-- 10. Deal × Partner (M2M)
CREATE TABLE IF NOT EXISTS nx_deal_partner (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    deal_id         INTEGER NOT NULL REFERENCES nx_deal(id) ON DELETE CASCADE,
    partner_id      INTEGER NOT NULL REFERENCES nx_partner(id),
    role            TEXT,          -- e.g., 'vision_provider', 'iot_vendor', 'si'
    created_at      TEXT DEFAULT (datetime('now')),
    UNIQUE(deal_id, partner_id)
);

-- 11. Deal × Intel (M2M)
CREATE TABLE IF NOT EXISTS nx_deal_intel (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    deal_id         INTEGER NOT NULL REFERENCES nx_deal(id) ON DELETE CASCADE,
    intel_id        INTEGER NOT NULL REFERENCES nx_intel(id) ON DELETE CASCADE,
    created_at      TEXT DEFAULT (datetime('now')),
    UNIQUE(deal_id, intel_id)
);

-- 12. Meetings (calendar events linked to deals)
CREATE TABLE IF NOT EXISTS nx_meeting (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    deal_id         INTEGER NOT NULL REFERENCES nx_deal(id),
    title           TEXT NOT NULL,
    meeting_date    TEXT NOT NULL,  -- ISO datetime
    duration_minutes INTEGER NOT NULL DEFAULT 60,
    participants_json TEXT,        -- JSON array of contact IDs + names
    location        TEXT,
    notes           TEXT,
    status          TEXT NOT NULL DEFAULT 'scheduled',  -- scheduled, completed, cancelled
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_nx_meeting_deal ON nx_meeting(deal_id);
CREATE INDEX IF NOT EXISTS idx_nx_meeting_date ON nx_meeting(meeting_date);

-- 13. Reminders (push/follow-up on calendar)
CREATE TABLE IF NOT EXISTS nx_reminder (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    deal_id         INTEGER REFERENCES nx_deal(id),
    reminder_type   TEXT NOT NULL,  -- 'push' (idle deal), 'document' (NDA expiry), 'tbd' (pending items), 'custom'
    due_date        TEXT NOT NULL,
    content         TEXT NOT NULL,
    resolved        INTEGER NOT NULL DEFAULT 0,
    resolved_at     TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_nx_reminder_due ON nx_reminder(due_date, resolved);

-- 14. Files (uploaded files + AI parse results)
CREATE TABLE IF NOT EXISTS nx_file (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    deal_id         INTEGER REFERENCES nx_deal(id),
    intel_id        INTEGER REFERENCES nx_intel(id),
    file_type       TEXT NOT NULL,  -- 'proposal', 'contract', 'attachment'
    file_name       TEXT NOT NULL,
    file_path       TEXT NOT NULL,
    file_size       INTEGER,
    source_url      TEXT,          -- Google Drive URL if applicable
    parsed_json     TEXT,          -- AI parse: {summary, pricing, roi, key_specs}
    parse_status    TEXT DEFAULT 'pending',  -- pending, parsed, failed, skipped
    created_at      TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_nx_file_deal ON nx_file(deal_id);
CREATE INDEX IF NOT EXISTS idx_nx_file_intel ON nx_file(intel_id);

-- 15. Intel ↔ Entity M2M (auto-materialized links)
CREATE TABLE IF NOT EXISTS nx_intel_entity (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    intel_id    INTEGER NOT NULL REFERENCES nx_intel(id) ON DELETE CASCADE,
    entity_type TEXT NOT NULL,  -- 'client', 'partner', 'contact', 'deal'
    entity_id   INTEGER NOT NULL,
    relation    TEXT DEFAULT 'mentioned',  -- 'mentioned', 'created_from'
    created_at  TEXT DEFAULT (datetime('now')),
    UNIQUE(intel_id, entity_type, entity_id)
);

-- 16. Intel parsed_json flattened index
CREATE TABLE IF NOT EXISTS nx_intel_field (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    intel_id    INTEGER NOT NULL REFERENCES nx_intel(id) ON DELETE CASCADE,
    field_key   TEXT NOT NULL,
    field_value TEXT NOT NULL,
    UNIQUE(intel_id, field_key, field_value)
);
CREATE INDEX IF NOT EXISTS idx_intel_field_kv ON nx_intel_field(field_key, field_value);

-- 17. Subsidy tracking (government grants / subsidies)
CREATE TABLE IF NOT EXISTS nx_subsidy (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,                  -- 計畫名稱
    source          TEXT,                           -- 來源管道
    agency          TEXT,                           -- 主辦機關
    program_type    TEXT NOT NULL DEFAULT 'other',  -- sbir, siir, local, other
    eligibility     TEXT,                           -- 申請資格
    funding_amount  TEXT,                           -- 補助額度 (text for ranges like "50-100萬")
    scope           TEXT,                           -- 申請範疇
    required_docs   TEXT,                           -- 申請文件
    deadline        TEXT,                           -- 申請截止 (ISO date)
    reference_url   TEXT,                           -- 資料來源 URL
    stage           TEXT NOT NULL DEFAULT 'draft',  -- draft→evaluating→applying→under_review→approved/rejected→executing→completed
    client_id       INTEGER REFERENCES nx_client(id),
    partner_id      INTEGER REFERENCES nx_partner(id),
    notes           TEXT,
    status          TEXT NOT NULL DEFAULT 'active',
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_nx_subsidy_stage ON nx_subsidy(status, stage);
CREATE INDEX IF NOT EXISTS idx_nx_subsidy_deadline ON nx_subsidy(deadline);

-- 18b. Subsidy deadlines (multiple batches per subsidy)
CREATE TABLE IF NOT EXISTS nx_subsidy_deadline (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    subsidy_id  INTEGER NOT NULL REFERENCES nx_subsidy(id) ON DELETE CASCADE,
    label       TEXT NOT NULL,           -- e.g. "第一梯", "第二梯"
    deadline_date TEXT NOT NULL,         -- ISO date (YYYY-MM-DD)
    notes       TEXT,
    status      TEXT NOT NULL DEFAULT 'open',  -- open, closed
    created_at  TEXT DEFAULT (datetime('now')),
    updated_at  TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_nx_subsidy_deadline_subsidy ON nx_subsidy_deadline(subsidy_id);
CREATE INDEX IF NOT EXISTS idx_nx_subsidy_deadline_date ON nx_subsidy_deadline(deadline_date, status);

-- 19. Subsidy × Deal (M2M)
CREATE TABLE IF NOT EXISTS nx_subsidy_deal (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    subsidy_id  INTEGER NOT NULL REFERENCES nx_subsidy(id) ON DELETE CASCADE,
    deal_id     INTEGER NOT NULL REFERENCES nx_deal(id) ON DELETE CASCADE,
    created_at  TEXT DEFAULT (datetime('now')),
    UNIQUE(subsidy_id, deal_id)
);
