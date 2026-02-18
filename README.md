# SPMS — B2B 業務與專案管理系統

Sales & Project Management System：為 B2B 業務團隊設計的售前/售後全流程管理工具。

## 功能特色

- **售前管線管理** — L0 客戶開發 → L7 簽約，狀態機自動追蹤案件進度
- **MEDDIC 關卡機制** — 在售前流程中導入 MEDDIC 框架，確保推進品質 (S25)
- **AI 智慧記錄** — 透過自然語言，自動建立客戶、工作日誌與專案 (S18-S22)
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
| Database | PostgreSQL 16（Docker） |
| AI 輔助 | Gemini（API for intelligent parsing） |

## Quick Start

```bash
# 1. 複製 .env.example 為 .env，並填入您的 GOOGLE_API_KEY
cp .env.example .env

# 2. 啟動 PostgreSQL
docker-compose up -d

# 3. 安裝 Python 套件
pip install -r requirements.txt

# 4. 初始化資料庫（自動建立所有表 + 執行冪等遷移）
python -c "from database.connection import init_db; init_db()"

# 5. 載入測試資料（選用）
python database/seed.py

# 6. 啟動應用程式
streamlit run app.py
```

> **升級既有 DB？** `init_db()` 已包含所有冪等 (idempotent) 遷移，升級時只需重新執行此指令即可。

## 專案結構

```
sales-assistant/
├── app.py                  # Streamlit 入口
├── prompts.yml             # AI 系統提示管理 (S22)
├── constants.py            # 狀態碼、轉換規則、權重閾值
├── check_models.py         # AI 模型可用性診斷腳本 (S20)
├── components/
│   └── sidebar.py          # 分組式側邊欄導航
├── database/
│   ├── connection.py       # psycopg2 連線池 + init_db()
│   ├── schema.sql          # DDL + Idempotent Migrations
│   └── seed.py             # 測試資料
├── services/               # 商業邏輯層（raw SQL CRUD）
│   ├── crm.py              # 客戶 CRUD + 自動建立
│   ├── project.py          # 專案 CRUD + 狀態機 + MEDDIC 關卡
│   ├── project_task.py     # 任務 CRUD + 統計 + Burndown
│   ├── work_log.py         # 工作日誌 CRUD
│   ├── sales_plan.py       # 商機計畫 CRUD
│   ├── contact.py          # 聯絡人 CRUD
│   ├── client_health.py    # 客戶健康分數
│   ├── intelligent_log.py  # AI 自然語言解析服務 (S18)
│   ├── meddic.py           # MEDDIC 資料服務 (S25)
│   └── ...
├── pages/                  # Streamlit 頁面
│   ├── work_log.py         # 工作日誌（含 AI 記錄功能）
│   ├── presale_detail.py   # 售前案件詳情（含 MEDDIC 面板）
│   └── ...
└── docs/
    ├── DEVELOPMENT_PLAN.md # 完整開發計畫
    ├── SPRINT_GUIDE.md     # Sprint 方法論
    └── sprints/S01-S25.md  # 各 Sprint 規格與 DoD
```

## 資料庫架構

14 張表，以 `project_list` 為中心：

| 表名 | 用途 |
|------|------|
| `annual_plan` | 年度產品策略與配額 |
| `crm` | 客戶主檔 |
| `project_list` | 案件/專案（中心表） |
| `project_meddic` | 專案的 MEDDIC 分析 (S25) |
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
特殊: LOST（遺失）、HOLD（擱置）
關卡: 各階段轉換可被 MEDDIC 項目完成度所限制 (S25)
```

## Sprint 進度

| Sprint | 主題 | 狀態 |
|--------|------|------|
| S01-S16 | 核心功能建設 | Done |
| S17 | Bug 維修與易用性優化（快速記錄） | Done |
| S18 | AI 智慧記錄 v1 (CRM & Work Log) | Done |
| S19 | API 金鑰 UX 優化 & AI 專案建立 | Done |
| S20 | AI 穩定性 Hotfix（模型名稱問題） | Done |
| S21 | DB 綱要同步 Hotfix (`sales_owner`) | Done |
| S22 | Prompt 管理重構 & 客戶 ID 生成修正 | Done |
| S23 | YAML Bug 修正 & 銷售流程優化 | Done |
| S24 | MEDDIC 關卡機制：設計與規劃 | Done |
| S25 | MEDDIC 關卡機制：實作開發 | Done |

## License

MIT
