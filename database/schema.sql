-- SPMS Database Schema (PostgreSQL)
-- 8 tables: 6 for Phase 1, 2 reserved for Phase 3

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
    email          TEXT,
    decision_maker JSONB,
    champion       JSONB,
    contact_info   TEXT,
    notes          TEXT,
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    updated_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS project_list (
    project_id        SERIAL PRIMARY KEY,
    project_name      TEXT NOT NULL,
    client_id         TEXT REFERENCES crm(client_id),
    product_id        TEXT REFERENCES annual_plan(product_id),
    status_code       TEXT NOT NULL DEFAULT 'S01',
    status_updated_at TIMESTAMPTZ DEFAULT NOW(),
    owner             TEXT,
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
    project_id     INTEGER NOT NULL REFERENCES project_list(project_id),
    log_date       DATE NOT NULL DEFAULT CURRENT_DATE,
    action_type    TEXT NOT NULL,
    content        TEXT,
    duration_hours NUMERIC NOT NULL DEFAULT 1.0,
    source         TEXT NOT NULL DEFAULT 'manual',
    ref_id         INTEGER,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app_settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

INSERT INTO app_settings (key, value) VALUES
    ('header_annual_plan', '年度戰略'),
    ('header_sales_plan', '商機預測'),
    ('header_pipeline', '業務漏斗'),
    ('header_crm', '客戶管理'),
    ('header_project', '專案管理'),
    ('header_work_log', '工作日誌')
ON CONFLICT (key) DO NOTHING;

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
