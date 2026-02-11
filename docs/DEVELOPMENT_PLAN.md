# SPMS - B2B 業務與專案管理系統 開發計畫

> **版本**: v1.2
> **建立日期**: 2026-02-10
> **技術架構**: Python + Streamlit + PostgreSQL
> **狀態**: Phase 2 完成（S07-S13）、客戶回饋改進完成（S14-S16）

## Context

建立一套 B2B 業務與專案管理系統，使用 **Python + Streamlit + PostgreSQL** 架構。目標是結構化追蹤業務進度、專案狀態與工作日誌，並為 AI Agent（持續運行 daemon）累積高品質決策數據。

### 架構決策紀錄
- **PostgreSQL 取代 SQLite**：Agent 為持續運行的 daemon，與 Streamlit 同時讀寫 DB，PostgreSQL 的併發處理更穩定
- **暫不引入 Redis**：PostgreSQL 的 LISTEN/NOTIFY 機制足以處理 Agent ↔ Streamlit 的即時通知
- **不使用 ORM**：直接使用 psycopg2 + 原始 SQL，PostgreSQL 是確定的最終方案，不需抽象層

---

## 1. 目錄結構

```
sales-assistant/
├── app.py                      # Streamlit 入口
├── requirements.txt            # 依賴套件
├── docker-compose.yml          # PostgreSQL 容器（開發環境）
├── .env                        # DB 連線資訊（不入版控）
├── .env.example                # 環境變數範本
├── docs/
│   ├── DEVELOPMENT_PLAN.md     # 本文件
│   ├── SPRINT_GUIDE.md         # Sprint 方法論指南
│   └── sprints/                # 各 Sprint 文件 (S01-S16)
├── database/
│   ├── __init__.py
│   ├── connection.py           # PostgreSQL 連線池管理 (psycopg2.pool)
│   ├── schema.sql              # 完整 CREATE TABLE DDL
│   ├── seed.py                 # 初始/示範資料
│   ├── migrate_crm_retro.py    # CRM 欄位遷移（champion→champions, DM 結構更新）
│   ├── migrate_s07.py          # S07 migration
│   ├── migrate_s08.py          # S08 migration
│   ├── migrate_s09.py          # S09 migration（project_task 表）
│   ├── migrate_s10.py          # S10 migration（contact 正規化）
│   ├── migrate_s11.py          # S11 migration（stage_probability + project_contact）
│   ├── migrate_s12.py          # S12 migration（due_date + is_next_action）
│   ├── migrate_s14.py          # S14 migration（work_log nullable project_id + client_id）
│   ├── migrate_s15.py          # S15 migration（JSONB vs 正規化驗證報告）
│   └── migrate_s16.py          # S16 migration（contact 去重 + UNIQUE INDEX）
├── models/
│   ├── __init__.py
│   └── schemas.py              # Pydantic 資料驗證模型
├── services/
│   ├── __init__.py
│   ├── annual_plan.py          # 年度戰略 CRUD
│   ├── sales_plan.py           # 商機預測 CRUD
│   ├── crm.py                  # 客戶關係 CRUD
│   ├── project.py              # 專案管理 CRUD + 狀態機（presale/postsale 共用）
│   ├── project_task.py         # 專案任務 CRUD
│   ├── contact.py              # 聯絡人 CRUD（S10 正規化）
│   ├── stage_probability.py    # 階段機率 CRUD（S11）
│   ├── search.py               # 全域搜尋服務（S13）
│   ├── work_log.py             # 工作日誌 CRUD（S14: 支援 client_id）
│   ├── client_health.py        # 客戶健康分數（S16）
│   └── settings.py             # 設定 CRUD
├── pages/
│   ├── work_log.py             # 工作日誌輸入中心
│   ├── annual_plan.py          # 年度戰略管理
│   ├── sales_plan.py           # 商機預測管理
│   ├── pipeline.py             # 業務漏斗 Dashboard
│   ├── crm.py                  # 客戶管理（含部門、詳情頁）
│   ├── presale.py              # 案件管理（L0-L7）
│   ├── postsale.py             # 專案管理（P0-P2）
│   ├── postsale_detail.py      # 售後專案明細（task CRUD / Gantt / Burndown）
│   ├── presale_detail.py       # 售前專案明細（狀態流轉 / 聯絡人 / 商機 / 時間軸）
│   ├── post_closure.py         # 已結案客戶（P2/LOST/HOLD）
│   ├── kanban.py               # 售前看板（L0-L6 欄位式佈局）
│   ├── search.py               # 全域搜尋（跨表 ILIKE）
│   └── settings.py             # 設定頁（修改 Header + 階段機率）
├── components/
│   ├── __init__.py
│   └── sidebar.py              # 共用側邊欄元件
├── constants.py                # 狀態碼、動作類型等常數
├── agent/                      # Phase 3（目錄先建立）
│   ├── __init__.py
│   ├── runner.py               # Agent daemon 主迴圈
│   ├── email_client.py         # Gmail API 收發信
│   ├── context_builder.py      # 組裝專案脈絡
│   ├── decision_engine.py      # Claude API 決策引擎
│   ├── executor.py             # 執行已核准動作
│   └── prompts/
│       ├── analyze_email.py
│       ├── draft_reply.py
│       └── assess_progress.py
└── data/                       # 本地資料（不入版控）
```

---

## 2. 資料庫 Schema（13 張表，PostgreSQL）

> Phase 1-2 建立全部 13 張表（11 張核心 + Phase 3 預留的 email_log、agent_actions），確保 Schema 一次到位。

### PostgreSQL 相較 SQLite 的優勢
- `JSONB` 原生型別：可直接查詢 JSON 內容（如 `decision_maker->>'style'`）
- `SERIAL`：自動遞增主鍵
- `TIMESTAMPTZ`：時區感知的時間戳
- `BOOLEAN`：原生布林值
- `LISTEN/NOTIFY`：Agent ↔ Streamlit 即時通知（Phase 3）
- 併發安全：daemon Agent + Streamlit 同時讀寫無問題

### 2.1 `annual_plan` — 年度戰略表

| 欄位 | 型別 | 說明 |
|------|------|------|
| product_id | TEXT PK | 產品唯一碼 |
| product_name | TEXT NOT NULL | 產品名稱 |
| quota_fy26 | NUMERIC | 年度業績目標 |
| strategy | TEXT | 攻案策略描述（RAG 知識庫來源） |
| target_industry | TEXT | 鎖定產業 |
| created_at | TIMESTAMPTZ | 建立時間 |
| updated_at | TIMESTAMPTZ | 更新時間 |

```sql
CREATE TABLE IF NOT EXISTS annual_plan (
    product_id      TEXT PRIMARY KEY,
    product_name    TEXT NOT NULL,
    quota_fy26      NUMERIC NOT NULL DEFAULT 0,
    strategy        TEXT,
    target_industry TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### 2.2 `crm` — 客戶關係表

| 欄位 | 型別 | 說明 |
|------|------|------|
| client_id | TEXT PK | 企業識別碼 |
| company_name | TEXT NOT NULL | 公司名稱 |
| industry | TEXT | 產業別 |
| department | TEXT | 部門（如：麥寮廠 碼槽處） |
| email | TEXT | 主要聯絡 email（Agent 比對寄件人用） |
| decision_maker | JSONB | 決策者 `{"name":"...", "title":"...", "email":"...", "phone":"...", "notes":"..."}` |
| champions | JSONB | 內部擁護者陣列 `[{"name":"...", "title":"...", "email":"...", "phone":"...", "notes":"..."}, ...]` |
| contact_info | TEXT | 聯絡資訊 |
| notes | TEXT | 備註 |
| data_year | INTEGER | 資料年份 |
| created_at | TIMESTAMPTZ | 建立時間 |
| updated_at | TIMESTAMPTZ | 更新時間 |

```sql
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
```

### 2.3 `project_list` — 專案總表（核心樞紐）

| 欄位 | 型別 | 說明 |
|------|------|------|
| project_id | SERIAL PK | 專案流水號 |
| project_name | TEXT NOT NULL | 專案名稱 |
| client_id | TEXT FK → crm | 客戶 ID |
| product_id | TEXT FK → annual_plan | 產品 ID |
| status_code | TEXT | 狀態碼（見狀態機） |
| status_updated_at | TIMESTAMPTZ | 狀態更新時間（用於停滯偵測） |
| presale_owner | TEXT | 售前負責人 |
| sales_owner | TEXT | 業務負責人 |
| postsale_owner | TEXT | 售後負責人 |
| priority | TEXT | 優先級 (High/Medium/Low) |
| created_at | TIMESTAMPTZ | 建立時間 |
| updated_at | TIMESTAMPTZ | 更新時間 |

```sql
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
```

### 2.4 `sales_plan` — 商機預測表

| 欄位 | 型別 | 說明 |
|------|------|------|
| plan_id | SERIAL PK | 流水號 |
| project_id | INTEGER FK → project_list | 關聯專案 |
| product_id | TEXT FK → annual_plan | 關聯產品 |
| expected_invoice_date | DATE | 預計開票日 |
| amount | NUMERIC | 金額 |
| confidence_level | NUMERIC (0~1) | 信心指數 |
| prime_contractor | BOOLEAN | 是否主標 |
| notes | TEXT | 備註 |
| created_at | TIMESTAMPTZ | 建立時間 |
| updated_at | TIMESTAMPTZ | 更新時間 |

```sql
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
```

### 2.5 `work_log` — 工作日誌表（AI 訓練燃料）

| 欄位 | 型別 | 說明 |
|------|------|------|
| log_id | SERIAL PK | 流水號 |
| project_id | INTEGER FK → project_list (nullable) | 關聯專案（S14 改 nullable） |
| client_id | TEXT FK → crm (nullable) | 關聯客戶（S14 新增） |
| log_date | DATE | 日誌日期 |
| action_type | TEXT | 會議/提案/開發/文件/郵件 |
| content | TEXT | 工作內容（完整保存，供 NLP） |
| duration_hours | NUMERIC | 工時（預設 1.0） |
| source | TEXT | 'manual'（人工）/ 'agent'（Agent 自動） |
| ref_id | INTEGER | 關聯的 email_id（Agent 自動建立時） |
| created_at | TIMESTAMPTZ | 建立時間 |

> **S14 變更**：`project_id` 改為 nullable，新增 `client_id` FK。CHECK 約束確保至少一個有值。支援不綁定專案的客戶活動。

```sql
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
```

### 2.6 `app_settings` — 系統設定表（自訂 Header）

| 欄位 | 型別 | 說明 |
|------|------|------|
| key | TEXT PK | 設定鍵 |
| value | TEXT NOT NULL | 設定值 |

```sql
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
```

### 2.7 `project_task` — 專案任務分項表

| 欄位 | 型別 | 說明 |
|------|------|------|
| task_id | SERIAL PK | 流水號 |
| project_id | INTEGER FK → project_list | 關聯專案（ON DELETE CASCADE） |
| task_name | TEXT NOT NULL | 任務名稱 |
| owner | TEXT | 負責人 |
| status | TEXT | 任務狀態（planned/in_progress/completed） |
| start_date | DATE | 開始日期 |
| end_date | DATE | 結束日期 |
| due_date | DATE | 截止日期（S12 新增） |
| is_next_action | BOOLEAN | 是否為下一步行動（S12 新增） |
| estimated_hours | NUMERIC | 預估工時 |
| actual_hours | NUMERIC | 實際工時 |
| sort_order | INTEGER | 排序順序 |
| created_at | TIMESTAMPTZ | 建立時間 |
| updated_at | TIMESTAMPTZ | 更新時間 |

```sql
CREATE TABLE IF NOT EXISTS project_task (
    task_id         SERIAL PRIMARY KEY,
    project_id      INTEGER NOT NULL REFERENCES project_list(project_id)
                    ON DELETE CASCADE,
    task_name       TEXT NOT NULL,
    owner           TEXT,
    status          TEXT NOT NULL DEFAULT 'planned',
    start_date      DATE,
    end_date        DATE,
    due_date        DATE,
    is_next_action  BOOLEAN NOT NULL DEFAULT FALSE,
    estimated_hours NUMERIC NOT NULL DEFAULT 0,
    actual_hours    NUMERIC NOT NULL DEFAULT 0,
    sort_order      INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### 2.8 `contact` — 聯絡人表（S10 正規化）

| 欄位 | 型別 | 說明 |
|------|------|------|
| contact_id | SERIAL PK | 流水號 |
| name | TEXT NOT NULL | 姓名 |
| title | TEXT | 職稱 |
| email | TEXT | Email |
| phone | TEXT | 電話 |
| notes | TEXT | 備註 |
| created_at | TIMESTAMPTZ | 建立時間 |
| updated_at | TIMESTAMPTZ | 更新時間 |

```sql
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

-- S16: 防止重複聯絡人
CREATE UNIQUE INDEX IF NOT EXISTS contact_name_email_unique
ON contact (name, COALESCE(email, ''));
```

### 2.9 `account_contact` — 客戶-聯絡人關聯表（S10 正規化）

| 欄位 | 型別 | 說明 |
|------|------|------|
| client_id | TEXT FK → crm | 客戶 ID（ON DELETE CASCADE） |
| contact_id | INTEGER FK → contact | 聯絡人 ID（ON DELETE CASCADE） |
| role | TEXT | 角色（decision_maker / champion） |
| sort_order | INTEGER | 排序順序 |

```sql
CREATE TABLE IF NOT EXISTS account_contact (
    client_id    TEXT NOT NULL REFERENCES crm(client_id) ON DELETE CASCADE,
    contact_id   INTEGER NOT NULL REFERENCES contact(contact_id) ON DELETE CASCADE,
    role         TEXT NOT NULL DEFAULT 'champion',
    sort_order   INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (client_id, contact_id)
);
```

> **S15 更新**：JSONB 雙寫已退場。`services/crm.py` 的 `create()` 和 `update()` 僅寫入正規化表（contact + account_contact）。`get_all()` 改用 LEFT JOIN 從正規化表讀取。JSONB 欄位（decision_maker, champions）保留為歷史參考，不再寫入。

### 2.10 `stage_probability` — 階段機率表（S11 新增）

| 欄位 | 型別 | 說明 |
|------|------|------|
| status_code | TEXT PK | 狀態碼（L0-L7, P0-P2, LOST, HOLD） |
| probability | NUMERIC (0~1) | 預設成交機率 |
| sort_order | INTEGER | 排序順序 |

```sql
CREATE TABLE IF NOT EXISTS stage_probability (
    status_code  TEXT PRIMARY KEY,
    probability  NUMERIC NOT NULL DEFAULT 0
        CHECK (probability >= 0 AND probability <= 1),
    sort_order   INTEGER NOT NULL DEFAULT 0
);

INSERT INTO stage_probability (status_code, probability, sort_order) VALUES
    ('L0', 0.05, 1), ('L1', 0.10, 2), ('L2', 0.20, 3), ('L3', 0.30, 4),
    ('L4', 0.50, 5), ('L5', 0.60, 6), ('L6', 0.75, 7), ('L7', 1.00, 8),
    ('P0', 1.00, 9), ('P1', 1.00, 10), ('P2', 1.00, 11),
    ('LOST', 0.00, 12), ('HOLD', 0.05, 13)
ON CONFLICT (status_code) DO NOTHING;
```

### 2.11 `project_contact` — 專案-聯絡人關聯表（S11 新增）

| 欄位 | 型別 | 說明 |
|------|------|------|
| project_id | INTEGER FK → project_list | 專案 ID（ON DELETE CASCADE） |
| contact_id | INTEGER FK → contact | 聯絡人 ID（ON DELETE CASCADE） |
| role | TEXT | 角色（participant / champion / decision_maker） |

```sql
CREATE TABLE IF NOT EXISTS project_contact (
    project_id   INTEGER NOT NULL REFERENCES project_list(project_id) ON DELETE CASCADE,
    contact_id   INTEGER NOT NULL REFERENCES contact(contact_id) ON DELETE CASCADE,
    role         TEXT NOT NULL DEFAULT 'participant',
    PRIMARY KEY (project_id, contact_id)
);
```

### 2.12 `email_log` — 郵件紀錄表（Phase 3 使用，Phase 1 建表）

| 欄位 | 型別 | 說明 |
|------|------|------|
| email_id | SERIAL PK | 流水號 |
| project_id | INTEGER FK → project_list | 關聯專案 |
| client_id | TEXT FK → crm | 關聯客戶 |
| direction | TEXT | 'inbound' / 'outbound' |
| from_addr | TEXT | 寄件人 |
| to_addr | TEXT | 收件人 |
| subject | TEXT | 主旨 |
| body | TEXT | 完整內容 |
| message_id | TEXT UNIQUE | Email Message-ID（對話串追蹤） |
| in_reply_to | TEXT | 回覆哪封信 |
| thread_id | TEXT | Gmail thread ID |
| status | TEXT | received / draft / approved / sent |
| created_at | TIMESTAMPTZ | 建立時間 |

```sql
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
```

### 2.13 `agent_actions` — Agent 動作佇列（Phase 3 使用，Phase 1 建表）

| 欄位 | 型別 | 說明 |
|------|------|------|
| action_id | SERIAL PK | 流水號 |
| project_id | INTEGER FK → project_list | 關聯專案 |
| trigger_type | TEXT | 'email_inbound' / 'scheduled' / 'stagnation' |
| trigger_ref | INTEGER | 觸發來源 ID |
| action_type | TEXT | 'draft_email' / 'update_status' / 'create_log' / 'alert' |
| action_data | JSONB | 動作細節 |
| status | TEXT | pending / approved / edited / rejected / executed |
| reviewed_by | TEXT | 審核者 |
| reviewed_at | TIMESTAMPTZ | 審核時間 |
| executed_at | TIMESTAMPTZ | 執行時間 |
| created_at | TIMESTAMPTZ | 建立時間 |

```sql
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
```

**`action_data` JSONB 範例**：
```json
// draft_email
{"to": "wang@tsmc.com", "subject": "Re: 定價方案", "body": "...", "reasoning": "..."}
// update_status
{"current_status": "L1", "proposed_status": "L2", "confidence": 0.85, "reasoning": "..."}
// alert
{"severity": "high", "message": "專案停滯 21 天，建議跟進"}
```

---

## 3. 狀態機設計（State Machine）

### 狀態碼定義

**售前 (Pre-sale) L0-L7：**

| 代碼 | 名稱 | 說明 |
|------|------|------|
| L0 | 客戶開發 | 初始接觸、發掘商機 |
| L1 | 等待追蹤 | 持續跟進中 |
| L2 | 提案 | 已完成 first call，提出方案 |
| L3 | 確認意願 | 客戶有意願，內部立案 |
| L4 | 執行 POC | 概念驗證進行中 |
| L5 | 完成 POC | 概念驗證結束 |
| L6 | 議價 | 價格協商 |
| L7 | 簽約 | 合約簽署（售前終態） |

**售後 (Post-sale) P0-P2：**

| 代碼 | 名稱 | 說明 |
|------|------|------|
| P0 | 規劃 | 交付規劃 |
| P1 | 執行 | 交付執行中 |
| P2 | 驗收 | 客戶驗收（售後終態） |

**特殊狀態：**

| 代碼 | 名稱 | 說明 |
|------|------|------|
| LOST | 遺失 | 案件遺失 |
| HOLD | 擱置 | 暫時擱置 |

### 合法狀態轉換

```
售前: L0 → L1 → L2 → L3 → L4 → L5 → L6 → L7
      所有 L0-L6 階段均可轉為 LOST 或 HOLD

轉換點: L7（簽約完成）→ P0（進入售後規劃），由售後負責人接手

售後: P0 → P1 → P2
      售後一旦進入則不可回退
```

### 非活躍狀態（不顯示在 Work Log 專案選單）
- `L7`（已簽約）
- `P2`（已驗收）
- `LOST`（已遺失）
- `HOLD`（已擱置）

---

## 4. 前端頁面設計

### 導航架構

使用 `st.navigation()` API，在 `app.py` 中統一定義所有頁面。頁面標題從 `app_settings` 表讀取，實現動態自訂 Header。Sidebar 採分組導航架構（`_NAV_SECTIONS`）。

### 導航結構

```
SPMS
├── 工作日誌              [standalone]
├── 年度戰略              [section → 產品策略管理]
├── 售前管理              [section → 5 sub-pages]
│   ├── 案件管理 (presale.py)
│   ├── 商機預測 (sales_plan.py)
│   ├── 業務漏斗 (pipeline.py)
│   ├── 售前看板 (kanban.py)
│   └── 客戶管理 (crm.py)
├── 售後管理              [section → 專案管理]
├── 客戶關係管理          [section → 已結案客戶]
├── 全域搜尋              [standalone]
└── 設定                  [standalone]
```

### 頁面清單

| # | 檔案 | 預設標題 | 功能 |
|---|------|---------|------|
| 1 | `pages/work_log.py` | 工作日誌 | 每日工作紀錄輸入（主力頁面）+ 今日待辦提醒 |
| 2 | `pages/annual_plan.py` | 產品策略管理 | 產品與策略管理 |
| 3 | `pages/presale.py` | 案件管理 | 售前案件 CRUD + L0-L7 狀態流轉 + 查看詳情按鈕 |
| 4 | `pages/sales_plan.py` | 商機預測 | 業績與開票預測 + 階段機率預填 |
| 5 | `pages/pipeline.py` | 業務漏斗 | Dashboard 戰情室 + 逾期待辦 + 機率加權預測 |
| 6 | `pages/crm.py` | 客戶管理 | 客戶與利害關係人（含部門、詳情頁、近期活動摘要） |
| 7 | `pages/postsale.py` | 專案管理 | 售後案件 CRUD + P0-P2 狀態流轉 |
| 8 | `pages/post_closure.py` | 已結案客戶 | 結案專案（P2/LOST/HOLD）依客戶分組 |
| 9 | `pages/settings.py` | 設定 | 自訂頁面 Header + 階段機率設定 |
| 10 | `pages/postsale_detail.py` | 專案詳情 | 售後專案明細（task CRUD / Gantt / Burndown + due_date / is_next_action） |
| 11 | `pages/presale_detail.py` | 案件詳情 | 售前專案明細（狀態流轉 / 關聯聯絡人 / 商機預測 / 活動時間軸 / 任務管理） |
| 12 | `pages/search.py` | 全域搜尋 | 跨表搜尋（聯絡人 / 客戶 / 專案）+ smart routing 至詳情頁 |
| 13 | `pages/kanban.py` | 售前看板 | L0-L6 欄位式看板 + 停滯警示 + 快速推進按鈕 |

### 頁面 1：工作日誌輸入中心（低摩擦、高效率）

- **專案選擇器**：下拉選單，自動過濾 INACTIVE_STATUSES
  - 顯示格式：`[L1] TSMC AI 客服導入案`
- **智慧表單**：
  - 日期：date_input，預設今天
  - 工時：number_input，預設 1.0 小時，步進 0.5
  - 工作類型：selectbox（會議/提案/開發/文件/郵件）
  - 內容描述：text_area，寬敞空間
- **即時反饋**：送出後下方顯示最近 5 筆紀錄（dataframe）

### 頁面 2-3：售前/售後管理

- **售前管理**：只顯示 L0-L7 + LOST + HOLD 狀態案件，有售前負責人欄位
- **售後管理**：只顯示 P0-P2 狀態案件，有售後負責人欄位
- 上方：資料列表（st.dataframe，可排序）
- 下方：新增/編輯/狀態流轉 tabs（只顯示合法的下一步狀態）

### 頁面 4-6：資料表 CRUD 管理頁

- 上方：資料列表（st.dataframe，可排序）
- 下方：新增/編輯表單（st.form）
- CRM 頁面：客戶詳情 tab 可查看完整 DM/Champion 資訊，列表只顯示姓名

### 頁面 7：業務漏斗 Dashboard

- **漏斗圖**：各階段（L 售前 / P 售後 / LOST / HOLD）案件數量（Plotly bar chart）
- **停滯警示**：`status_updated_at` 距今 > 14 天的案件標紅顯示
- **業績預測表**：基於 sales_plan，列出本月/下月預計開票的案子與金額

### 頁面 9：設定頁

- 8 個 text_input，分別對應 8 個頁面的 Header 標題
- 「儲存」按鈕，寫入 `app_settings` 表
- 儲存後頁面 rerun，側邊欄標題立即更新

---

## 5. 開發任務與順序（Phase 1）

> **Sprint 開發流程**：Phase 1 已拆分為 6 個 Sprint，每個 Sprint 遵循五階段工作流（Kickoff → Planning → Vibe Coding → Review → Retro/Refactor）。
> 詳見 [Sprint 方法論指南](SPRINT_GUIDE.md) 與 [各 Sprint 文件](sprints/)。
>
> | Sprint | 標題 | 文件 |
> |--------|------|------|
> | S01 | Infrastructure Foundation | [S01.md](sprints/S01.md) |
> | S02 | Data Layer | [S02.md](sprints/S02.md) |
> | S03 | Core Pages | [S03.md](sprints/S03.md) |
> | S04 | Supporting Pages | [S04.md](sprints/S04.md) |
> | S05 | Dashboard & Settings | [S05.md](sprints/S05.md) |
> | S06 | Integration & Polish | [S06.md](sprints/S06.md) |
> | S07 | Customer Feedback Sprint | [S07.md](sprints/S07.md) |
> | S08 | Navigation Restructuring | [S08.md](sprints/S08.md) |
> | S09 | Work Log Split + Postsale Detail | [S09.md](sprints/S09.md) |
> | S10 | DB Normalization (Contact) | [S10.md](sprints/S10.md) |
> | S11 | 階段機率 + Deal-Contact + 售前詳情頁 | [S11.md](sprints/S11.md) |
> | S12 | 活動時間軸 + 售前任務 + 下一步行動 | [S12.md](sprints/S12.md) |
> | S13 | 全域搜尋 + Visual Board | [S13.md](sprints/S13.md) |
> | S14 | 客戶層級活動記錄 | [S14.md](sprints/S14.md) |
> | S15 | 客戶營收彙總 + JSONB 退場 | [S15.md](sprints/S15.md) |
> | S16 | 客戶健康分數 + 聯絡人去重 | [S16.md](sprints/S16.md) |

### Step 1：基礎建設
| # | 任務 | 檔案 |
|---|------|------|
| 1.1 | 建立專案骨架與依賴 | `requirements.txt`, `docker-compose.yml`, `.env.example`, 各 `__init__.py` |
| 1.2 | 定義常數（狀態碼、動作類型） | `constants.py` |
| 1.3 | 撰寫資料庫 DDL | `database/schema.sql`（13 張表，PostgreSQL 語法） |
| 1.4 | 實作 DB 連線池與初始化 | `database/connection.py`（psycopg2.pool） |

### Step 2：資料模型與服務層
| # | 任務 | 檔案 |
|---|------|------|
| 2.1 | 定義 Pydantic 驗證模型 | `models/schemas.py` |
| 2.2 | 實作各表 CRUD 服務 | `services/*.py`（6 個檔案） |

### Step 3：前端頁面
| # | 任務 | 檔案 |
|---|------|------|
| 3.1 | 工作日誌頁面 | `pages/work_log.py` |
| 3.2 | 專案管理頁面（含狀態機 UI） | `pages/project.py` |
| 3.3 | 年度戰略頁面 | `pages/annual_plan.py` |
| 3.4 | 客戶管理頁面 | `pages/crm.py` |
| 3.5 | 商機預測頁面 | `pages/sales_plan.py` |
| 3.6 | 業務漏斗 Dashboard | `pages/pipeline.py` |
| 3.7 | 設定頁面（自訂 Header） | `pages/settings.py` |

### Step 4：整合與測試
| # | 任務 | 檔案 |
|---|------|------|
| 4.1 | 主入口整合所有頁面 | `app.py` |
| 4.2 | 建立示範資料 | `database/seed.py` |
| 4.3 | 端到端測試 | 手動驗證 |

---

## 6. Phase 2 增強

**已完成：**
- S07：客戶回饋 Sprint — CRM 欄位重構（champion→champions, DM 結構更新, data_year）
- S08：導航重構 — 分組側邊欄、presale/postsale 分離、post_closure 頁面
- S09：Work Log 分頁 + 售後詳情頁（postsale_detail.py，含 task CRUD / Gantt / Burndown）
- S10：DB 正規化 — Contact 獨立表（contact + account_contact），雙寫策略
- S11：階段機率 + Deal-Contact + 售前詳情頁 — stage_probability 表、project_contact 表、presale_detail.py、機率預填
- S12：活動時間軸 + 售前任務 + 下一步行動 — due_date / is_next_action、今日待辦提醒、逾期警示、近期活動摘要
- S13：全域搜尋 + Visual Board — 跨表 ILIKE 搜尋、售前看板（L0-L6 欄位式 Kanban）

**客戶回饋改進（S14-S16）：**
- S14：客戶層級活動 — work_log nullable project_id + client_id FK、radio toggle、UNION 查詢
- S15：營收彙總 + JSONB 退場 — get_summary_by_client()、get_all() LEFT JOIN、停止 JSONB 雙寫
- S16：健康分數 + 聯絡人去重 — client_health.py 4 維度評分、contact UNIQUE INDEX、upsert

**規劃中：**
- Dashboard 加強 — 趨勢線、工時分析圖表
- 匯出與批次操作 — Excel/CSV 匯出、批次狀態更新

## 7. Phase 3 — AI Sales Agent 架構

### 7.1 Agent 三大能力

| 能力 | 說明 | 實現方式 |
|------|------|---------|
| 收信 | 監控客戶來信、自動歸檔至專案 | Gmail API 持續輪詢 |
| 發信 | 代擬回覆郵件、人工審核後發送 | Claude API 生成 + Gmail API 發送 |
| 推進度 | 建議狀態推進、偵測停滯警示 | Claude API 分析脈絡 + 結構化提案 |

### 7.2 核心原則：Human-in-the-Loop

**Agent 提案，人類決策。** 所有對外動作（發信、改狀態）必須經人工審核。

### 7.3 Agent 運行架構

```
Gmail API (收發信)
       ↓
Email Client (agent/email_client.py)
       ↓
Context Builder (agent/context_builder.py)
  - 比對寄件人 → CRM client_id
  - 關聯活躍專案
  - 拉取：work_log + email_log + project status + strategy + CRM
       ↓
Decision Engine (agent/decision_engine.py)
  - 呼叫 Claude API
  - 輸出結構化動作提案
       ↓
Action Queue (agent_actions 表)
  - status: pending → approved/rejected → executed
       ↓
Streamlit Agent 控制台 (pages/agent.py)
  - 人工審核：核准 / 編輯 / 駁回
```

### 7.4 三大工作流程

#### 流程 A：收信 → 自動歸檔 → 提議回覆
1. Agent daemon 持續輪詢 Gmail
2. 新郵件 → 比對 `crm.email` → 找到 client_id → 關聯活躍專案
3. 存入 `email_log` + 自動建 `work_log`（source='agent'）
4. 組裝完整脈絡 → Claude API 分析 → 生成回覆草稿 + 狀態建議
5. 寫入 `agent_actions`（pending）→ 人工審核 → 執行

#### 流程 B：定時掃描 → 停滯偵測 → 推進建議
1. Agent 定時檢查 `status_updated_at` 超過閾值的案件
   - L 系列 > 14 天 / P 系列 > 21 天
2. Claude 分析脈絡 → 建議推進/HOLD/LOST/具體行動
3. 寫入 `agent_actions` → 人工審核

#### 流程 C：人工觸發 → Agent 代擬郵件
1. 使用者在 Agent 控制台選擇專案 + 輸入指示
2. Claude 生成郵件草稿 → 使用者預覽/編輯 → 核准發送

### 7.5 Agent 目錄結構
```
agent/
├── __init__.py
├── runner.py              # Daemon 主迴圈（持續運行）
├── email_client.py        # Gmail API 收發信封裝
├── context_builder.py     # 組裝專案脈絡給 Claude
├── decision_engine.py     # 呼叫 Claude API，解析回應
├── executor.py            # 執行已核准的動作
└── prompts/
    ├── analyze_email.py   # 分析來信
    ├── draft_reply.py     # 擬稿回覆
    └── assess_progress.py # 評估進度
```

### 7.6 Agent 控制台頁面（pages/agent.py）
- 待審核佇列：顯示 pending 的 agent_actions
- 每筆動作顯示：觸發原因、信心指數、推理過程
- 操作按鈕：核准 / 編輯後核准 / 駁回
- 郵件預覽：draft_email 動作可預覽完整信件內容

### 7.7 Phase 1 預留接口

| 預留項目 | 位置 | 說明 |
|---------|------|------|
| `crm.email` 欄位 | schema.sql | Phase 1 就加入，UI 提供輸入 |
| `work_log.source` 欄位 | schema.sql | Phase 1 就加入，預設 'manual' |
| `work_log.ref_id` 欄位 | schema.sql | Phase 1 就加入，可為 NULL |
| `email_log` 表 | schema.sql | Phase 1 建表，Phase 3 寫入 |
| `agent_actions` 表 | schema.sql | Phase 1 建表，Phase 3 寫入 |

### 7.8 未來 Agent 進階能力
1. **自動週報**：每週五讀取 work_log + email_log，生成摘要
2. **競爭情報**：分析郵件中的競品關鍵字
3. **最佳時機**：根據歷史回覆時間建議聯絡時段
4. **風險預警**：偵測負面情緒郵件，預警案件可能轉 LOST

---

## 8. 驗證方式

### Phase 1 驗證
1. `docker-compose up -d` 啟動 PostgreSQL
2. `streamlit run app.py` 啟動應用
3. 確認 PostgreSQL 中 13 張表存在
4. 在設定頁修改任一 Header → 確認側邊欄標題即時更新
5. 新增一筆專案 → 在工作日誌頁下拉選單看到該專案
6. 新增工作日誌 → 確認最近 5 筆顯示正確
7. 在專案管理頁操作狀態流轉 → 確認只能選合法的下一步
8. Dashboard 漏斗圖正確反映各階段案件數

### Phase 3 驗證
1. 設定 Gmail API credentials → Agent 成功收取測試郵件
2. 收到客戶來信 → email_log + work_log 自動建立
3. Agent 提案出現在控制台 → 核准後郵件成功發送
4. 停滯專案觸發警示 → 狀態推進建議出現在控制台
