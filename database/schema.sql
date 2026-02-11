-- SPMS Database Schema (PostgreSQL)
-- 13 tables: 11 core + 2 reserved for Phase 3

CREATE TABLE IF NOT EXISTS annual_plan (
    product_id      TEXT PRIMARY KEY,
    product_name    TEXT NOT NULL,
    quota_fy26      NUMERIC NOT NULL DEFAULT 0,
    strategy        TEXT,
    target_industry TEXT,
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
    ('header_post_closure', '已結案客戶')
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
