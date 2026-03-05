-- SPMS / Project Nexus Database Schema (SQLite)
-- Adapted from PostgreSQL schema.sql

CREATE TABLE IF NOT EXISTS annual_plan (
    product_id      TEXT PRIMARY KEY,
    product_name    TEXT NOT NULL,
    quota_fy26      REAL NOT NULL DEFAULT 0,
    strategy        TEXT,
    target_industry TEXT,
    pillar          TEXT,
    owner           TEXT,
    kpis            TEXT,
    status          TEXT NOT NULL DEFAULT 'Q2 計劃',
    battlefront     TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS crm (
    client_id      TEXT PRIMARY KEY,
    company_name   TEXT NOT NULL,
    industry       TEXT,
    department     TEXT,
    email          TEXT,
    decision_maker TEXT,
    champions      TEXT,
    contact_info   TEXT,
    notes          TEXT,
    data_year      INTEGER,
    client_health_score INTEGER DEFAULT 75,
    created_at     TEXT DEFAULT (datetime('now')),
    updated_at     TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS project_list (
    project_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name      TEXT NOT NULL,
    client_id         TEXT REFERENCES crm(client_id),
    product_id        TEXT REFERENCES annual_plan(product_id),
    status_code       TEXT NOT NULL DEFAULT 'L0',
    status_updated_at TEXT DEFAULT (datetime('now')),
    presale_owner     TEXT,
    sales_owner       TEXT,
    postsale_owner    TEXT,
    priority          TEXT DEFAULT 'Medium',
    channel           TEXT,
    created_at        TEXT DEFAULT (datetime('now')),
    updated_at        TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sales_plan (
    plan_id               INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id            INTEGER NOT NULL REFERENCES project_list(project_id),
    product_id            TEXT REFERENCES annual_plan(product_id),
    expected_invoice_date TEXT,
    amount                REAL NOT NULL DEFAULT 0,
    confidence_level      REAL NOT NULL DEFAULT 0.5
        CHECK (confidence_level >= 0 AND confidence_level <= 1),
    prime_contractor      INTEGER NOT NULL DEFAULT 1,
    notes                 TEXT,
    created_at            TEXT DEFAULT (datetime('now')),
    updated_at            TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS work_log (
    log_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id     INTEGER REFERENCES project_list(project_id),
    client_id      TEXT REFERENCES crm(client_id),
    log_date       TEXT NOT NULL DEFAULT (date('now')),
    action_type    TEXT NOT NULL,
    content        TEXT,
    duration_hours REAL NOT NULL DEFAULT 1.0,
    source         TEXT NOT NULL DEFAULT 'manual',
    ref_id         INTEGER,
    created_at     TEXT DEFAULT (datetime('now')),
    CHECK (project_id IS NOT NULL OR client_id IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS project_task (
    task_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER NOT NULL REFERENCES project_list(project_id)
                    ON DELETE CASCADE,
    task_name       TEXT NOT NULL,
    owner           TEXT,
    status          TEXT NOT NULL DEFAULT 'planned',
    start_date      TEXT,
    end_date        TEXT,
    estimated_hours REAL NOT NULL DEFAULT 0,
    actual_hours    REAL NOT NULL DEFAULT 0,
    sort_order      INTEGER NOT NULL DEFAULT 0,
    due_date        TEXT,
    is_next_action  INTEGER DEFAULT 0,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS app_settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

INSERT OR IGNORE INTO app_settings (key, value) VALUES
    ('header_work_log', '工作日誌'),
    ('header_presale', '案件管理'),
    ('header_postsale', '專案管理'),
    ('header_annual_plan', '產品策略管理'),
    ('header_sales_plan', '商機預測'),
    ('header_crm', '客戶管理'),
    ('header_pipeline', '業務漏斗'),
    ('header_post_closure', '已結案客戶'),
    ('hourly_cost_rate', '100');

-- Contact normalization (S10)

CREATE TABLE IF NOT EXISTS contact (
    contact_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL,
    title        TEXT,
    email        TEXT,
    phone        TEXT,
    notes        TEXT,
    created_at   TEXT DEFAULT (datetime('now')),
    updated_at   TEXT DEFAULT (datetime('now'))
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

-- Stage probability (S11)

CREATE TABLE IF NOT EXISTS stage_probability (
    status_code  TEXT PRIMARY KEY,
    probability  REAL NOT NULL DEFAULT 0.5
        CHECK (probability >= 0 AND probability <= 1),
    sort_order   INTEGER NOT NULL DEFAULT 0
);

INSERT OR IGNORE INTO stage_probability (status_code, probability, sort_order) VALUES
    ('L0', 0.05, 1), ('L1', 0.10, 2), ('L2', 0.20, 3), ('L3', 0.30, 4),
    ('L4', 0.50, 5), ('L5', 0.60, 6), ('L6', 0.75, 7), ('L7', 1.00, 8),
    ('P0', 1.00, 9), ('P1', 1.00, 10), ('P2', 1.00, 11),
    ('LOST', 0.00, 12), ('HOLD', 0.05, 13);

CREATE TABLE IF NOT EXISTS project_contact (
    project_id   INTEGER NOT NULL REFERENCES project_list(project_id) ON DELETE CASCADE,
    contact_id   INTEGER NOT NULL REFERENCES contact(contact_id) ON DELETE CASCADE,
    role         TEXT NOT NULL DEFAULT 'participant',
    PRIMARY KEY (project_id, contact_id)
);

-- MEDDIC (S25)

CREATE TABLE IF NOT EXISTS project_meddic (
    project_id               INTEGER PRIMARY KEY REFERENCES project_list(project_id) ON DELETE CASCADE,
    metrics                  TEXT,
    economic_buyer           TEXT,
    decision_criteria        TEXT,
    decision_process         TEXT,
    identify_pain            TEXT,
    champion                 TEXT,
    updated_at               TEXT DEFAULT (datetime('now'))
);

-- Async AI task queue (S29)

CREATE TABLE IF NOT EXISTS ai_task_queue (
    task_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    status         TEXT NOT NULL DEFAULT 'pending',
    raw_text       TEXT NOT NULL,
    result_data    TEXT,
    error_message  TEXT,
    created_at     TEXT DEFAULT (datetime('now')),
    processed_at   TEXT
);

-- Phase 3 reserved tables

CREATE TABLE IF NOT EXISTS email_log (
    email_id    INTEGER PRIMARY KEY AUTOINCREMENT,
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
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS agent_actions (
    action_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id   INTEGER REFERENCES project_list(project_id),
    trigger_type TEXT NOT NULL,
    trigger_ref  INTEGER,
    action_type  TEXT NOT NULL,
    action_data  TEXT NOT NULL,
    status       TEXT DEFAULT 'pending',
    reviewed_by  TEXT,
    reviewed_at  TEXT,
    executed_at  TEXT,
    created_at   TEXT DEFAULT (datetime('now'))
);

-- S33: Nexus tables

CREATE TABLE IF NOT EXISTS stakeholder_relation (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    from_contact_id INTEGER NOT NULL REFERENCES contact(contact_id) ON DELETE CASCADE,
    to_contact_id   INTEGER NOT NULL REFERENCES contact(contact_id) ON DELETE CASCADE,
    relation_type   TEXT NOT NULL,
    notes           TEXT,
    leverage_value  TEXT DEFAULT 'medium',
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS intel (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    title             TEXT NOT NULL,
    summary           TEXT,
    leverage_value    TEXT DEFAULT 'medium',
    source_contact_id INTEGER REFERENCES contact(contact_id),
    created_at        TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS intel_org (
    intel_id INTEGER NOT NULL REFERENCES intel(id) ON DELETE CASCADE,
    crm_id   TEXT NOT NULL REFERENCES crm(client_id) ON DELETE CASCADE,
    PRIMARY KEY (intel_id, crm_id)
);
