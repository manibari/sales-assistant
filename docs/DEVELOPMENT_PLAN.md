# SPMS - B2B 業務與專案管理系統 開發計畫

> **版本**: v1.3
> **建立日期**: 2026-02-10
> **狀態**: Phase 2 & 迭代開發完成（S07-S25）

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
    ├── DEVELOPMENT_PLAN.md # 本文件
    ├── SPRINT_GUIDE.md     # Sprint 方法論
    └── sprints/S01-S25.md  # 各 Sprint 規格與 DoD
```

---

## 2. 資料庫 Schema（14 張表，PostgreSQL）

> Phase 1-2 + 迭代開發，共建立 14 張表（12 張核心 + 2 張 Phase 3 預留）。

*此處省略各資料表詳細定義，請參考 `README.md` 或 `database/schema.sql`*

---

## 3. 狀態機設計（State Machine）

*此處省略狀態機細節，請參考 `README.md`*

---

## 4. 前端頁面設計

*此處省略頁面設計細節，請參考 `README.md`*

---

## 5. 開發任務與順序（Phase 1）

*此處省略 Phase 1 (S01-S06) 的詳細任務，請參考 `README.md`*

---

## 6. Phase 2 增強

*此處省略 Phase 2 (S07-S16) 的詳細任務，請參考 `README.md`*

---

## 7. Phase 3 — AI Sales Agent 架構

*此處為原始的 AI Agent 規劃，部分功能已在迭代開發中以「AI 智慧記錄」的形式提前實現。*

*...（其餘 Phase 3 原始規劃省略）...*

---

## 8. 迭代開發成果 (S17-S25)

在完成了 S01-S16 的基礎建設後，專案進入了更靈活的迭代開發階段。這個階段的特點是根據使用者的即時回饋，快速地修復 Bug、優化體驗，並湧現出計畫外的新功能。

### 8.1 AI 智慧記錄 (S18, S19, S20, S22)

這是在迭代過程中實現的、一個輕量級但強大的 AI 功能，可視為原始「Phase 3」規劃的提前落地與簡化版。

- **核心功能**: 使用者可以在一個專用的 UI 中輸入自然語言的工作日誌。系統會呼叫 Gemini API，從文字中自動解析出客戶名稱、專案名稱、初始狀態等，並在 `crm`, `work_log`, `project_list` 等多個資料表中自動建立對應的紀錄。
- **演進過程**:
    - **S18**: 建立核心功能，實現了對客戶和工作日誌的自動建立。
    - **S19**: 擴充功能，加入了自動建立專案 (Project) 的能力。
    - **S20**: 穩定性提升，在多次 Hotfix 中，透過建立診斷腳本 (`check_models.py`) 徹底解決了因環境差異導致的 API 模型名稱 `404` 錯誤。
    - **S22**: 架構重構，將硬編碼的 Prompt 抽離至獨立的 `prompts.yml` 檔案，並修正了客戶 ID 的生成邏輯，使其更具擴充性與專業性。

### 8.2 MEDDIC 關卡機制 (S24, S25)

這是在迭代過程中，根據使用者提出的「加強銷售流程紀律」需求而誕生的全新功能。

- **核心功能**: 為售前流程引入了 MEDDIC 銷售框架。系統在案件詳情頁提供了專門的「MEDDIC」面板供業務填寫。在推進專案狀態時，後端會進行「關卡驗證」，確保推進到下一階段前，當前階段必要的 MEDDIC 項目都已完成，從而提升銷售過程的品質。
- **演進過程**:
    - **S24 (設計 Sprint)**: 專門用一個 Sprint 進行完整的技術規劃，包括定義新的 `project_meddic` 資料表、前端 UI/UX 設計、後端驗證邏輯，以及明確的「關卡規則」。
    - **S25 (實作 Sprint)**: 根據 S24 的設計藍圖，完成了包含資料庫、後端服務、前端介面和核心邏輯在內的完整開發工作。
