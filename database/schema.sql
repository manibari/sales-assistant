-- SPMS + Project Nexus Database Schema (PostgreSQL / Supabase)
-- All tables unified into a single schema file.

-- =========================================================================
-- Legacy SPMS Tables (Phase 1-3)
-- =========================================================================

CREATE TABLE IF NOT EXISTS annual_plan (
    product_id      TEXT PRIMARY KEY,
    product_name    TEXT NOT NULL,
    quota_fy26      NUMERIC NOT NULL DEFAULT 0,
    strategy        TEXT,
    target_industry TEXT,
    pillar          TEXT,
    owner           TEXT,
    kpis            TEXT,
    status          TEXT NOT NULL DEFAULT 'Q2 計劃',
    battlefront     TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS crm (
    client_id      TEXT PRIMARY KEY,
    company_name   TEXT NOT NULL,
    industry       TEXT,
    department     TEXT,
    email          TEXT,
    decision_maker JSONB,       -- {name, title, email, phone, notes}
    champions      JSONB,       -- [{name, title, email, phone, notes}, ...]
    contact_info   TEXT,
    notes          TEXT,
    data_year      INTEGER,
    client_health_score INTEGER DEFAULT 75,
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    updated_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS project_list (
    project_id        SERIAL PRIMARY KEY,
    project_name      TEXT NOT NULL,
    client_id         TEXT REFERENCES crm(client_id),
    product_id        TEXT REFERENCES annual_plan(product_id),
    status_code       TEXT NOT NULL DEFAULT 'L0',
    status_updated_at TIMESTAMPTZ DEFAULT NOW(),
    presale_owner     TEXT,
    sales_owner       TEXT,
    postsale_owner    TEXT,
    priority          TEXT DEFAULT 'Medium',
    channel           TEXT,
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    updated_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sales_plan (
    plan_id               SERIAL PRIMARY KEY,
    project_id            INTEGER NOT NULL REFERENCES project_list(project_id),
    product_id            TEXT REFERENCES annual_plan(product_id),
    expected_invoice_date DATE,
    amount                NUMERIC NOT NULL DEFAULT 0,
    confidence_level      NUMERIC NOT NULL DEFAULT 0.5
        CHECK (confidence_level >= 0 AND confidence_level <= 1),
    prime_contractor      BOOLEAN NOT NULL DEFAULT TRUE,
    notes                 TEXT,
    created_at            TIMESTAMPTZ DEFAULT NOW(),
    updated_at            TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS work_log (
    log_id         SERIAL PRIMARY KEY,
    project_id     INTEGER REFERENCES project_list(project_id),
    client_id      TEXT REFERENCES crm(client_id),
    log_date       DATE NOT NULL DEFAULT CURRENT_DATE,
    action_type    TEXT NOT NULL,
    content        TEXT,
    duration_hours NUMERIC NOT NULL DEFAULT 1.0,
    source         TEXT NOT NULL DEFAULT 'manual',
    ref_id         INTEGER,
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT work_log_scope_check CHECK (project_id IS NOT NULL OR client_id IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS project_task (
    task_id         SERIAL PRIMARY KEY,
    project_id      INTEGER NOT NULL REFERENCES project_list(project_id)
                    ON DELETE CASCADE,
    task_name       TEXT NOT NULL,
    owner           TEXT,
    status          TEXT NOT NULL DEFAULT 'planned',
    start_date      DATE,
    end_date        DATE,
    estimated_hours NUMERIC NOT NULL DEFAULT 0,
    actual_hours    NUMERIC NOT NULL DEFAULT 0,
    sort_order      INTEGER NOT NULL DEFAULT 0,
    due_date        DATE,
    is_next_action  BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app_settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

INSERT INTO app_settings (key, value) VALUES
    ('header_work_log', '工作日誌'),
    ('header_presale', '案件管理'),
    ('header_postsale', '專案管理'),
    ('header_annual_plan', '產品策略管理'),
    ('header_sales_plan', '商機預測'),
    ('header_crm', '客戶管理'),
    ('header_pipeline', '業務漏斗'),
    ('header_post_closure', '已結案客戶'),
    ('hourly_cost_rate', '100')
ON CONFLICT (key) DO NOTHING;

-- S10: Contact normalization tables

CREATE TABLE IF NOT EXISTS contact (
    contact_id   SERIAL PRIMARY KEY,
    name         TEXT NOT NULL,
    title        TEXT,
    email        TEXT,
    phone        TEXT,
    notes        TEXT,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    updated_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS contact_name_email_unique
ON contact (name, COALESCE(email, ''));

CREATE TABLE IF NOT EXISTS account_contact (
    client_id    TEXT NOT NULL REFERENCES crm(client_id) ON DELETE CASCADE,
    contact_id   INTEGER NOT NULL REFERENCES contact(contact_id) ON DELETE CASCADE,
    role         TEXT NOT NULL DEFAULT 'champion',
    sort_order   INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (client_id, contact_id)
);

-- S11: Stage probability + project-contact linking

CREATE TABLE IF NOT EXISTS stage_probability (
    status_code  TEXT PRIMARY KEY,
    probability  NUMERIC NOT NULL DEFAULT 0.5
        CHECK (probability >= 0 AND probability <= 1),
    sort_order   INTEGER NOT NULL DEFAULT 0
);

INSERT INTO stage_probability (status_code, probability, sort_order) VALUES
    ('L0', 0.05, 1), ('L1', 0.10, 2), ('L2', 0.20, 3), ('L3', 0.30, 4),
    ('L4', 0.50, 5), ('L5', 0.60, 6), ('L6', 0.75, 7), ('L7', 1.00, 8),
    ('P0', 1.00, 9), ('P1', 1.00, 10), ('P2', 1.00, 11),
    ('LOST', 0.00, 12), ('HOLD', 0.05, 13)
ON CONFLICT (status_code) DO NOTHING;

CREATE TABLE IF NOT EXISTS project_contact (
    project_id   INTEGER NOT NULL REFERENCES project_list(project_id) ON DELETE CASCADE,
    contact_id   INTEGER NOT NULL REFERENCES contact(contact_id) ON DELETE CASCADE,
    role         TEXT NOT NULL DEFAULT 'participant',
    PRIMARY KEY (project_id, contact_id)
);

-- S25: MEDDIC table
CREATE TABLE IF NOT EXISTS project_meddic (
    project_id               INTEGER PRIMARY KEY REFERENCES project_list(project_id) ON DELETE CASCADE,
    metrics                  TEXT,
    economic_buyer           TEXT,
    decision_criteria        TEXT,
    decision_process         TEXT,
    identify_pain            TEXT,
    champion                 TEXT,
    updated_at               TIMESTAMPTZ DEFAULT NOW()
);

-- S29: Asynchronous AI task queue
CREATE TABLE IF NOT EXISTS ai_task_queue (
    task_id        SERIAL PRIMARY KEY,
    status         TEXT NOT NULL DEFAULT 'pending',
    raw_text       TEXT NOT NULL,
    result_data    JSONB,
    error_message  TEXT,
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    processed_at   TIMESTAMPTZ
);

-- Phase 3 reserved tables

CREATE TABLE IF NOT EXISTS email_log (
    email_id    SERIAL PRIMARY KEY,
    project_id  INTEGER REFERENCES project_list(project_id),
    client_id   TEXT REFERENCES crm(client_id),
    direction   TEXT NOT NULL,
    from_addr   TEXT NOT NULL,
    to_addr     TEXT NOT NULL,
    subject     TEXT,
    body        TEXT,
    message_id  TEXT UNIQUE,
    in_reply_to TEXT,
    thread_id   TEXT,
    status      TEXT DEFAULT 'received',
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_actions (
    action_id    SERIAL PRIMARY KEY,
    project_id   INTEGER REFERENCES project_list(project_id),
    trigger_type TEXT NOT NULL,
    trigger_ref  INTEGER,
    action_type  TEXT NOT NULL,
    action_data  JSONB NOT NULL,
    status       TEXT DEFAULT 'pending',
    reviewed_by  TEXT,
    reviewed_at  TIMESTAMPTZ,
    executed_at  TIMESTAMPTZ,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- S33: Nexus tables -- stakeholder relationships + intelligence leverage
CREATE TABLE IF NOT EXISTS stakeholder_relation (
    id              SERIAL PRIMARY KEY,
    from_contact_id INTEGER NOT NULL REFERENCES contact(contact_id) ON DELETE CASCADE,
    to_contact_id   INTEGER NOT NULL REFERENCES contact(contact_id) ON DELETE CASCADE,
    relation_type   TEXT NOT NULL,
    notes           TEXT,
    leverage_value  TEXT DEFAULT 'medium',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS intel (
    id                SERIAL PRIMARY KEY,
    title             TEXT NOT NULL,
    summary           TEXT,
    leverage_value    TEXT DEFAULT 'medium',
    source_contact_id INTEGER REFERENCES contact(contact_id),
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS intel_org (
    intel_id INTEGER NOT NULL REFERENCES intel(id) ON DELETE CASCADE,
    crm_id   TEXT NOT NULL REFERENCES crm(client_id) ON DELETE CASCADE,
    PRIMARY KEY (intel_id, crm_id)
);

-- =========================================================================
-- Project Nexus Engine 1 Tables (Phase 4)
-- All tables prefixed nx_.
-- =========================================================================

-- 1. Client organizations
CREATE TABLE IF NOT EXISTS nx_client (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    industry        TEXT,
    aliases         TEXT,
    budget_range    TEXT,
    status          TEXT NOT NULL DEFAULT 'active',
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Partner organizations
CREATE TABLE IF NOT EXISTS nx_partner (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    trust_level     TEXT NOT NULL DEFAULT 'unverified',
    team_size       TEXT,
    aliases         TEXT,
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Contacts (people, linked to client OR partner)
CREATE TABLE IF NOT EXISTS nx_contact (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    title           TEXT,
    phone           TEXT,
    email           TEXT,
    line_id         TEXT,
    org_type        TEXT,
    org_id          INTEGER,
    role            TEXT,
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_nx_contact_org ON nx_contact(org_type, org_id);

-- 4. Intelligence entries (raw + parsed)
CREATE TABLE IF NOT EXISTS nx_intel (
    id              SERIAL PRIMARY KEY,
    title           TEXT,
    raw_input       TEXT NOT NULL,
    input_type      TEXT NOT NULL DEFAULT 'text',
    parsed_json     JSONB,
    chat_history    JSONB,
    status          TEXT NOT NULL DEFAULT 'draft',
    source_contact_id INTEGER REFERENCES nx_contact(id),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Universal tags
CREATE TABLE IF NOT EXISTS nx_tag (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    category        TEXT NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(name, category)
);

-- 6. Polymorphic tag join (entity_type + entity_id -> any entity)
CREATE TABLE IF NOT EXISTS nx_entity_tag (
    id              SERIAL PRIMARY KEY,
    entity_type     TEXT NOT NULL,
    entity_id       INTEGER NOT NULL,
    tag_id          INTEGER NOT NULL REFERENCES nx_tag(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(entity_type, entity_id, tag_id)
);
CREATE INDEX IF NOT EXISTS idx_nx_entity_tag_entity ON nx_entity_tag(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_nx_entity_tag_tag ON nx_entity_tag(tag_id);

-- 7. TBD items (skipped Q&A + meeting action items)
CREATE TABLE IF NOT EXISTS nx_tbd_item (
    id              SERIAL PRIMARY KEY,
    question        TEXT NOT NULL,
    context         TEXT,
    linked_type     TEXT,
    linked_id       INTEGER,
    source          TEXT NOT NULL DEFAULT 'skip',
    resolved        BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_nx_tbd_linked ON nx_tbd_item(linked_type, linked_id, resolved);

-- 8. Document tracking (NDA/MOU)
CREATE TABLE IF NOT EXISTS nx_document (
    id              SERIAL PRIMARY KEY,
    client_id       INTEGER NOT NULL REFERENCES nx_client(id),
    doc_type        TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending',
    sign_date       DATE,
    expiry_date     DATE,
    file_path       TEXT,
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_nx_document_client ON nx_document(client_id);

-- 9. Deals -- the CORE entity
CREATE TABLE IF NOT EXISTS nx_deal (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    client_id       INTEGER NOT NULL REFERENCES nx_client(id),
    stage           TEXT NOT NULL DEFAULT 'L0',
    budget_range    TEXT,
    budget_amount   NUMERIC,
    budget_year     INTEGER DEFAULT 2026,
    timeline        TEXT,
    meddic_json     JSONB,
    close_reason    TEXT,
    close_notes     TEXT,
    status          TEXT NOT NULL DEFAULT 'active',
    last_activity_at TIMESTAMPTZ DEFAULT NOW(),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_nx_deal_client ON nx_deal(client_id);
CREATE INDEX IF NOT EXISTS idx_nx_deal_status ON nx_deal(status, stage);

-- 10. Deal x Partner (M2M)
CREATE TABLE IF NOT EXISTS nx_deal_partner (
    id              SERIAL PRIMARY KEY,
    deal_id         INTEGER NOT NULL REFERENCES nx_deal(id) ON DELETE CASCADE,
    partner_id      INTEGER NOT NULL REFERENCES nx_partner(id),
    role            TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(deal_id, partner_id)
);

-- 11. Deal x Intel (M2M)
CREATE TABLE IF NOT EXISTS nx_deal_intel (
    id              SERIAL PRIMARY KEY,
    deal_id         INTEGER NOT NULL REFERENCES nx_deal(id) ON DELETE CASCADE,
    intel_id        INTEGER NOT NULL REFERENCES nx_intel(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(deal_id, intel_id)
);

-- 12. Meetings (calendar events linked to deals)
CREATE TABLE IF NOT EXISTS nx_meeting (
    id              SERIAL PRIMARY KEY,
    deal_id         INTEGER NOT NULL REFERENCES nx_deal(id),
    title           TEXT NOT NULL,
    meeting_date    TIMESTAMPTZ NOT NULL,
    duration_minutes INTEGER NOT NULL DEFAULT 60,
    participants_json JSONB,
    location        TEXT,
    notes           TEXT,
    status          TEXT NOT NULL DEFAULT 'scheduled',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_nx_meeting_deal ON nx_meeting(deal_id);
CREATE INDEX IF NOT EXISTS idx_nx_meeting_date ON nx_meeting(meeting_date);

-- 13. Reminders (push/follow-up on calendar)
CREATE TABLE IF NOT EXISTS nx_reminder (
    id              SERIAL PRIMARY KEY,
    deal_id         INTEGER REFERENCES nx_deal(id),
    reminder_type   TEXT NOT NULL,
    due_date        TIMESTAMPTZ NOT NULL,
    content         TEXT NOT NULL,
    resolved        BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_nx_reminder_due ON nx_reminder(due_date, resolved);

-- 14. Files (uploaded files + AI parse results)
CREATE TABLE IF NOT EXISTS nx_file (
    id              SERIAL PRIMARY KEY,
    deal_id         INTEGER REFERENCES nx_deal(id),
    intel_id        INTEGER REFERENCES nx_intel(id),
    file_type       TEXT NOT NULL,
    file_name       TEXT NOT NULL,
    file_path       TEXT NOT NULL,
    file_size       INTEGER,
    source_url      TEXT,
    parsed_json     JSONB,
    parse_status    TEXT DEFAULT 'pending',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_nx_file_deal ON nx_file(deal_id);
CREATE INDEX IF NOT EXISTS idx_nx_file_intel ON nx_file(intel_id);

-- 15. Intel <-> Entity M2M (auto-materialized links)
CREATE TABLE IF NOT EXISTS nx_intel_entity (
    id          SERIAL PRIMARY KEY,
    intel_id    INTEGER NOT NULL REFERENCES nx_intel(id) ON DELETE CASCADE,
    entity_type TEXT NOT NULL,
    entity_id   INTEGER NOT NULL,
    relation    TEXT DEFAULT 'mentioned',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(intel_id, entity_type, entity_id)
);

-- 16. Intel parsed_json flattened index
CREATE TABLE IF NOT EXISTS nx_intel_field (
    id          SERIAL PRIMARY KEY,
    intel_id    INTEGER NOT NULL REFERENCES nx_intel(id) ON DELETE CASCADE,
    field_key   TEXT NOT NULL,
    field_value TEXT NOT NULL,
    UNIQUE(intel_id, field_key, field_value)
);
CREATE INDEX IF NOT EXISTS idx_intel_field_kv ON nx_intel_field(field_key, field_value);

-- 17. Subsidy tracking (government grants / subsidies)
CREATE TABLE IF NOT EXISTS nx_subsidy (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    source          TEXT,
    agency          TEXT,
    program_type    TEXT NOT NULL DEFAULT 'other',
    eligibility     TEXT,
    funding_amount  TEXT,
    scope           TEXT,
    required_docs   TEXT,
    deadline        TEXT,
    reference_url   TEXT,
    stage           TEXT NOT NULL DEFAULT 'draft',
    client_id       INTEGER REFERENCES nx_client(id),
    partner_id      INTEGER REFERENCES nx_partner(id),
    deadline_date   DATE,
    notes           TEXT,
    status          TEXT NOT NULL DEFAULT 'active',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_nx_subsidy_stage ON nx_subsidy(status, stage);
CREATE INDEX IF NOT EXISTS idx_nx_subsidy_deadline ON nx_subsidy(deadline_date);

-- 18. Subsidy deadlines (multiple batches per subsidy)
CREATE TABLE IF NOT EXISTS nx_subsidy_deadline (
    id          SERIAL PRIMARY KEY,
    subsidy_id  INTEGER NOT NULL REFERENCES nx_subsidy(id) ON DELETE CASCADE,
    label       TEXT NOT NULL,
    deadline_date DATE NOT NULL,
    notes       TEXT,
    status      TEXT NOT NULL DEFAULT 'open',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_nx_subsidy_deadline_subsidy ON nx_subsidy_deadline(subsidy_id);
CREATE INDEX IF NOT EXISTS idx_nx_subsidy_deadline_date ON nx_subsidy_deadline(deadline_date, status);

-- 19. Subsidy x Deal (M2M)
CREATE TABLE IF NOT EXISTS nx_subsidy_deal (
    id          SERIAL PRIMARY KEY,
    subsidy_id  INTEGER NOT NULL REFERENCES nx_subsidy(id) ON DELETE CASCADE,
    deal_id     INTEGER NOT NULL REFERENCES nx_deal(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(subsidy_id, deal_id)
);
