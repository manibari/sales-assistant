# SPMS — B2B 業務與專案管理系統

Sales & Project Management System：為 B2B 業務團隊設計的售前/售後全流程管理工具。

## 功能特色

- **售前管線管理** — L0 客戶開發 → L7 簽約，8 階段狀態機自動追蹤案件進度
- **售後專案管理** — P0 規劃 → P2 驗收，任務排程、Gantt chart、Burndown chart
- **客戶關係管理 (CRM)** — 聯絡人正規化、決策者/Champion 管理、客戶健康分數
- **商機預測與漏斗** — Sales plan × 階段機率 = 加權營收預測，業務漏斗可視化
- **工作日誌** — 專案層級 + 客戶層級活動記錄，支援多種動作類型
- **全域搜尋** — 跨聯絡人、客戶、專案的即時搜尋

## Tech Stack

| 層級 | 技術 |
|------|------|
| Frontend | [Streamlit](https://streamlit.io/) |
| Backend | Python + psycopg2（raw SQL，無 ORM） |
| Database | PostgreSQL 15（Docker） |
| AI 輔助 | Claude Code（solo + AI-assisted 開發） |

## Quick Start

```bash
# 1. 啟動 PostgreSQL
docker-compose up -d

# 2. 安裝 Python 套件
pip install -r requirements.txt

# 3. 初始化資料庫（建立 13 張表 + 自動執行 idempotent migrations）
python -c "from database.connection import init_db; init_db()"

# 4. 載入測試資料（選用）
python database/seed.py

# 5. 啟動應用程式
streamlit run app.py
```

> **升級既有 DB？** `init_db()` 已包含 idempotent migration 區塊（S14/S16），無需手動執行 migration scripts。

## 專案結構

```
sales-assistant/
├── app.py                  # Streamlit 入口
├── constants.py            # 狀態碼、轉換規則、權重閾值
├── components/
│   └── sidebar.py          # 分組式側邊欄導航
├── database/
│   ├── connection.py       # psycopg2 連線池 + init_db()
│   ├── schema.sql          # 13 表 DDL + idempotent migrations
│   ├── seed.py             # 測試資料
│   └── migrate_*.py        # 各 Sprint 增量 migration
├── services/               # 商業邏輯層（raw SQL CRUD）
│   ├── crm.py              # 客戶 CRUD + 聯絡人同步
│   ├── project.py          # 案件 CRUD + 狀態機 + 聯絡人連結
│   ├── project_task.py     # 任務 CRUD + 統計 + Burndown
│   ├── work_log.py         # 工作日誌（專案/客戶層級）
│   ├── sales_plan.py       # 商機計畫 CRUD + 客戶彙總
│   ├── contact.py          # 聯絡人 CRUD + 帳戶連結
│   ├── client_health.py    # 客戶健康分數（0-100）
│   ├── search.py           # 全域搜尋
│   ├── annual_plan.py      # 年度產品策略 CRUD
│   ├── stage_probability.py # 階段機率 CRUD
│   └── settings.py         # 應用程式設定 CRUD
├── pages/                  # Streamlit 頁面
│   ├── work_log.py         # 工作日誌（首頁）
│   ├── crm.py              # 客戶管理 + 健康分數
│   ├── presale.py          # 售前案件列表
│   ├── presale_detail.py   # 售前案件詳情
│   ├── postsale.py         # 售後專案列表
│   ├── postsale_detail.py  # 售後專案詳情（Gantt/Burndown）
│   ├── sales_plan.py       # 商機預測
│   ├── pipeline.py         # 業務漏斗
│   ├── kanban.py           # 售前看板
│   ├── annual_plan.py      # 產品策略管理
│   ├── post_closure.py     # 已結案客戶
│   ├── search.py           # 全域搜尋
│   └── settings.py         # 設定（頁面標題、階段機率）
└── docs/
    ├── DEVELOPMENT_PLAN.md # 完整開發計畫
    ├── SPRINT_GUIDE.md     # Sprint 方法論
    └── sprints/S01-S16.md  # 各 Sprint 規格與 DoD
```

## 資料庫架構

13 張表，以 `project_list` 為中心：

| 表名 | 用途 |
|------|------|
| `annual_plan` | 年度產品策略與配額 |
| `crm` | 客戶主檔 |
| `project_list` | 案件/專案（中心表） |
| `sales_plan` | 商機計畫（金額、機率） |
| `work_log` | 工作日誌（專案/客戶層級） |
| `project_task` | 案件/專案任務 |
| `contact` | 聯絡人（正規化） |
| `account_contact` | 客戶↔聯絡人（多對多） |
| `project_contact` | 案件↔聯絡人（多對多） |
| `stage_probability` | 階段預設機率 |
| `app_settings` | 應用程式設定 |
| `email_log` | 郵件記錄（Phase 3 預留） |
| `agent_actions` | AI Agent 動作（Phase 3 預留） |

### 狀態機

```
售前: L0 客戶開發 → L1 等待追蹤 → L2 提案 → L3 確認意願 → L4 執行POC → L5 完成POC → L6 議價 → L7 簽約
售後: P0 規劃 → P1 執行 → P2 驗收
特殊: LOST（遺失）、HOLD（擱置）— L0~L6 均可轉換
```

## Sprint 進度

| Sprint | 主題 | 狀態 |
|--------|------|------|
| S01 | 專案初始化 + Docker + Schema | Done |
| S02 | 工作日誌 CRUD | Done |
| S03 | 年度策略管理 | Done |
| S04 | 售前管理 + 狀態機 | Done |
| S05 | 售後管理 + 任務系統 | Done |
| S06 | 商機預測 + 漏斗 | Done |
| S07 | CRM 客戶管理 | Done |
| S08 | 已結案客戶 + 設定 | Done |
| S09 | 售前詳情 + Kanban | Done |
| S10 | 聯絡人正規化 | Done |
| S11 | 階段機率 + 案件聯絡人 | Done |
| S12 | 任務到期日 + Next Action | Done |
| S13 | 售後詳情 + Gantt/Burndown | Done |
| S14 | 客戶層級活動記錄 | Done |
| S15 | JSONB 退役 + 正規化驗證 | Done |
| S16 | 聯絡人去重 + 客戶健康分數 | Done |

## License

MIT
