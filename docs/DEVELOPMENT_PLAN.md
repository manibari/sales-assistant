# SPMS - B2B 業務與專案管理系統 開發計畫

> **版本**: v1.1
> **建立日期**: 2026-02-10
> **技術架構**: Python + Streamlit + PostgreSQL
> **狀態**: Phase 1 開發中

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
│   └── DEVELOPMENT_PLAN.md     # 本文件
├── database/
│   ├── __init__.py
│   ├── connection.py           # PostgreSQL 連線池管理 (psycopg2.pool)
│   ├── schema.sql              # 完整 CREATE TABLE DDL
│   └── seed.py                 # 初始/示範資料
├── models/
│   ├── __init__.py
│   └── schemas.py              # Pydantic 資料驗證模型
├── services/
│   ├── __init__.py
│   ├── annual_plan.py          # 年度戰略 CRUD
│   ├── sales_plan.py           # 商機預測 CRUD
│   ├── crm.py                  # 客戶關係 CRUD
│   ├── project.py              # 專案管理 CRUD + 狀態機
│   ├── work_log.py             # 工作日誌 CRUD
│   └── settings.py             # 設定 CRUD
├── pages/
│   ├── work_log.py             # 工作日誌輸入中心
│   ├── annual_plan.py          # 年度戰略管理
│   ├── sales_plan.py           # 商機預測管理
│   ├── pipeline.py             # 業務漏斗 Dashboard
│   ├── crm.py                  # 客戶管理
│   ├── project.py              # 專案總表
│   └── settings.py             # 設定頁（修改 Header 等）
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

## 2. 資料庫 Schema（8 張表，PostgreSQL）

> Phase 1 建立全部 8 張表（含 Phase 3 預留的 email_log、agent_actions），確保 Schema 一次到位。

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
| email | TEXT | 主要聯絡 email（Agent 比對寄件人用） |
| decision_maker | JSONB | 決策者 `{"name":"...", "title":"...", "style":"..."}` |
| champion | JSONB | 內部擁護者 `{"name":"...", "title":"...", "notes":"..."}` |
| contact_info | TEXT | 聯絡資訊 |
| notes | TEXT | 備註 |
| created_at | TIMESTAMPTZ | 建立時間 |
| updated_at | TIMESTAMPTZ | 更新時間 |

```sql
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
| owner | TEXT | 負責人 |
| priority | TEXT | 優先級 (High/Medium/Low) |
| created_at | TIMESTAMPTZ | 建立時間 |
| updated_at | TIMESTAMPTZ | 更新時間 |

```sql
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
| project_id | INTEGER FK → project_list | 關聯專案 |
| log_date | DATE | 日誌日期 |
| action_type | TEXT | 會議/提案/開發/文件/郵件 |
| content | TEXT | 工作內容（完整保存，供 NLP） |
| duration_hours | NUMERIC | 工時（預設 1.0） |
| source | TEXT | 'manual'（人工）/ 'agent'（Agent 自動） |
| ref_id | INTEGER | 關聯的 email_id（Agent 自動建立時） |
| created_at | TIMESTAMPTZ | 建立時間 |

```sql
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
    ('header_annual_plan', '年度戰略'),
    ('header_sales_plan', '商機預測'),
    ('header_pipeline', '業務漏斗'),
    ('header_crm', '客戶管理'),
    ('header_project', '專案管理'),
    ('header_work_log', '工作日誌')
ON CONFLICT (key) DO NOTHING;
```

### 2.7 `email_log` — 郵件紀錄表（Phase 3 使用，Phase 1 建表）

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

### 2.8 `agent_actions` — Agent 動作佇列（Phase 3 使用，Phase 1 建表）

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
{"current_status": "S02", "proposed_status": "S03", "confidence": 0.85, "reasoning": "..."}
// alert
{"severity": "high", "message": "專案停滯 21 天，建議跟進"}
```

---

## 3. 狀態機設計（State Machine）

### 狀態碼定義

| 系列 | 代碼 | 名稱 | 說明 |
|------|------|------|------|
| S (Sales) | S01 | 開發 | 初始接觸、發掘商機 |
| | S02 | 追蹤 | 持續跟進中 |
| | S03 | 提案 | 已提出方案 |
| | S04 | 立案 | 正式立案追蹤 |
| T (Tech) | T01 | POC 執行 | 概念驗證進行中 |
| | T02 | POC 完成 | 概念驗證結束 |
| C (Closing) | C01 | 議價 | 價格協商 |
| | C02 | 條款 | 合約條款協商 |
| | C03 | 審查 | 內部審查流程 |
| | C04 | 簽約 | 合約簽署 |
| D (Delivery) | D01 | 規劃 | 交付規劃 |
| | D02 | 開發 | 交付開發中 |
| | D03 | 驗收 | 客戶驗收（終態） |
| 特殊 | LOST | 遺失 | 案件遺失 |
| | HOLD | 擱置 | 暫時擱置 |

### 合法狀態轉換

```
S01 → S02 → S03 → S04
                       ↘
                        T01 → T02
                       ↗         ↘
S04 ─────────────────→ C01 → C02 → C03 → C04 → D01 → D02 → D03
                       ↑
                       T02

所有 S/T/C 階段均可轉為 LOST 或 HOLD
D 系列一旦進入則不可回退
```

### 非活躍狀態（不顯示在 Work Log 專案選單）
- `D03`（已驗收）
- `LOST`（已遺失）
- `HOLD`（已擱置）

---

## 4. 前端頁面設計

### 導航架構

使用 `st.navigation()` API，在 `app.py` 中統一定義所有頁面。頁面標題從 `app_settings` 表讀取，實現動態自訂 Header。

### 頁面清單

| # | 檔案 | 預設標題 | 功能 |
|---|------|---------|------|
| 1 | `pages/work_log.py` | 工作日誌 | 每日工作紀錄輸入（主力頁面） |
| 2 | `pages/project.py` | 專案管理 | 專案 CRUD + 狀態流轉 |
| 3 | `pages/annual_plan.py` | 年度戰略 | 產品與策略管理 |
| 4 | `pages/sales_plan.py` | 商機預測 | 業績與開票預測 |
| 5 | `pages/crm.py` | 客戶管理 | 客戶與利害關係人 |
| 6 | `pages/pipeline.py` | 業務漏斗 | Dashboard 戰情室 |
| 7 | `pages/settings.py` | 設定 | 自訂頁面 Header |

### 頁面 1：工作日誌輸入中心（低摩擦、高效率）

- **專案選擇器**：下拉選單，自動過濾 INACTIVE_STATUSES
  - 顯示格式：`[S02] TSMC AI 客服導入案`
- **智慧表單**：
  - 日期：date_input，預設今天
  - 工時：number_input，預設 1.0 小時，步進 0.5
  - 工作類型：selectbox（會議/提案/開發/文件/郵件）
  - 內容描述：text_area，寬敞空間
- **即時反饋**：送出後下方顯示最近 5 筆紀錄（dataframe）

### 頁面 2-5：資料表 CRUD 管理頁

- 上方：資料列表（st.dataframe，可排序）
- 下方：新增/編輯表單（st.form）
- 專案總表特殊功能：狀態流轉按鈕（只顯示合法的下一步狀態）

### 頁面 6：業務漏斗 Dashboard

- **漏斗圖**：各階段（S/T/C/D）案件數量（Plotly bar chart）
- **停滯警示**：`status_updated_at` 距今 > 14 天的案件標紅顯示
- **業績預測表**：基於 sales_plan，列出本月/下月預計開票的案子與金額

### 頁面 7：設定頁

- 6 個 text_input，分別對應 6 個頁面的 Header 標題
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

### Step 1：基礎建設
| # | 任務 | 檔案 |
|---|------|------|
| 1.1 | 建立專案骨架與依賴 | `requirements.txt`, `docker-compose.yml`, `.env.example`, 各 `__init__.py` |
| 1.2 | 定義常數（狀態碼、動作類型） | `constants.py` |
| 1.3 | 撰寫資料庫 DDL | `database/schema.sql`（8 張表，PostgreSQL 語法） |
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

## 6. Phase 2 增強（未來）

- Dashboard 加入趨勢線、工時分析圖表
- 匯出功能（Excel / CSV）
- 進階篩選與搜尋
- 批次狀態更新

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
   - S 系列 > 14 天 / T 系列 > 21 天 / C 系列 > 7 天
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
3. 確認 PostgreSQL 中 8 張表存在
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
