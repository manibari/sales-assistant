# Sprint 方法論指南

> **適用對象**: SPMS 專案開發（AI-assisted Vibe Coding）
> **Sprint 週期**: 約 2.5 ~ 3 小時 / Sprint（含 10 分鐘 Kickoff）
> **總覽**: Phase 1 共拆為 6 個 Sprint（S01–S06）

---

## Sprint 五階段工作流

每個 Sprint 嚴格遵循以下五個階段，確保品質與節奏：

```
┌──────────────┐    ┌─────────────┐    ┌─────────────────┐    ┌──────────────┐    ┌──────────────────────┐
│   Stage 0    │ →  │  Stage 1    │ →  │    Stage 2      │ →  │   Stage 3    │ →  │      Stage 4         │
│   Kickoff    │    │  Planning   │    │  Vibe Coding    │    │   Review     │    │  Retro & Refactor    │
│   (10 min)   │    │  (15 min)   │    │  (90-120 min)   │    │   (15 min)   │    │     (30 min)         │
└──────────────┘    └─────────────┘    └─────────────────┘    └──────────────┘    └──────────────────────┘
```

### Stage 0: Sprint Kickoff（10 分鐘）

**目標**：對齊上下文、確認就緒、設定意圖。Solo + AI 情境下的「自我對齊」儀式。

- [ ] **前次 Sprint 回顧**：快速確認前一個 Sprint 的完成狀態與產出物
- [ ] **上下文載入**：重新載入心智模型（讀 DEVELOPMENT_PLAN 相關段落、前次 Sprint 的教訓）
- [ ] **本次 Sprint 目標宣告**：用一句話說明這個 Sprint 要達成什麼
- [ ] **前置條件檢查**：確認依賴的 Sprint 已完成、環境就緒
- [ ] **Session 意圖設定**：今天的精神狀態、時間預算、特別注意事項

**輸出物**：Sprint 文件的 Stage 0 區塊填寫完畢，確認進入 Planning 的準備就緒。

### Stage 1: Sprint Planning（15 分鐘）

**目標**：明確定義本次 Sprint 的範圍與驗收標準。

- [ ] 確認 User Stories（使用者故事）
- [ ] 確認 Definition of Done（完成定義）
- [ ] 準備 Context Files（餵給 AI 的參考檔案）
- [ ] 如有前一個 Sprint 的產出，確認其可用性

**輸出物**：Sprint 文件的 Stage 1 區塊填寫完畢。

### Stage 2: Vibe Coding（90–120 分鐘）

**目標**：快速開發，讓功能「先能動」。

- 以 User Stories 為導向，逐一實現
- 遇到阻塞時先用最簡方案繞過，標記 `// TODO` 待 Stage 4 處理
- 每完成一個 User Story 就做一次快速手動驗證
- **原則**：Make it work → Make it right（Stage 4）→ Make it fast（未來）

**輸出物**：所有 User Stories 功能可運作（可能有瑕疵）。

### Stage 3: Sprint Review（15 分鐘）

**目標**：對照 DoD 逐條驗證，找出未達標項目。

- [ ] 逐條檢查 Definition of Done
- [ ] 記錄發現的 Bug 或不符合項
- [ ] 確認所有 User Stories 皆已實現
- [ ] 更新 Sprint 文件的 Stage 3 區塊

**輸出物**：Review 結果記錄、Bug 清單。

### Stage 4: Sprint Retrospective & Refactor（30 分鐘）

**目標**：清理程式碼、修復 Bug、提交乾淨的 commit，並進行結構化反思。

#### Refactor 部分

- [ ] 修復 Stage 3 發現的 Bug
- [ ] 處理 Stage 2 標記的 `// TODO`
- [ ] 移除 debug 用的 print / console.log
- [ ] 確認程式碼風格一致
- [ ] 撰寫 commit message 並提交
- [ ] 更新 Sprint 狀態為 `completed`

#### Retro 部分（結構化反思）

- [ ] **What went well** — 本次做得好的、要繼續的
- [ ] **What didn't go well** — 遇到的困難、要避免的
- [ ] **Action items for next sprint** — 下次可以改善的具體行動
- [ ] **AI 協作筆記** — 哪些 prompt/context 有效、哪些無效
- [ ] **時間追蹤** — 預估 vs 實際耗時

**輸出物**：乾淨的 git commit、Sprint 文件更新為完成狀態、結構化反思紀錄。

---

## Sprint 文件模板

每個 Sprint 文件（`docs/sprints/S0X.md`）應遵循以下結構：

```markdown
# Sprint S0X — [標題]

> **狀態**: `pending` | `in_progress` | `completed`
> **預估時間**: X 小時
> **前置 Sprint**: S0Y（如適用）

---

## Stage 0: Sprint Kickoff

### 前次 Sprint 回顧

- 前次 Sprint: [S0Y / 無]
- 完成狀態: [確認項目]

### Sprint 目標宣告

> 用一句話說明：[本次 Sprint 要達成什麼]

### 前置條件檢查

- [ ] [依賴的 Sprint 已完成]
- [ ] [環境就緒]

### Session 意圖

- 精神狀態：（Sprint 開始時填寫）
- 時間預算：（Sprint 開始時填寫）
- 特別注意事項：（Sprint 開始時填寫）

---

## Stage 1: Sprint Planning

### User Stories

- [ ] **US-1**: 作為 [角色]，我希望 [功能]，以便 [價值]
- [ ] **US-2**: ...

### Definition of Done（完成定義）

- [ ] DoD-1: [具體可驗證的條件]
- [ ] DoD-2: ...

### Context Files（AI 參考檔案）

開始此 Sprint 前，將以下檔案提供給 AI：
- `docs/DEVELOPMENT_PLAN.md` — 總體架構參考
- `[其他相關檔案]`

---

## Stage 2: Vibe Coding

### 實作紀錄

> 在開發過程中記錄重要決策與遇到的問題。

- ...

### TODO / 技術債

- [ ] ...

---

## Stage 3: Sprint Review

### DoD 驗證結果

| # | 條件 | 通過? | 備註 |
|---|------|-------|------|
| 1 | ... | ✅/❌ | ... |

### 發現的問題

- ...

---

## Stage 4: Retrospective & Refactor

### 修復項目

- [ ] ...

### Retro: What went well

- ...

### Retro: What didn't go well

- ...

### Retro: Action items for next sprint

- [ ] ...

### Retro: AI 協作筆記

- 有效的 prompt/context：...
- 無效的 prompt/context：...

### Retro: 時間追蹤

- 預估時間：X 小時
- 實際時間：（Sprint 結束後填寫）
- 差異原因：（Sprint 結束後填寫）

### Git Commit

- commit hash: `[填入]`
- message: `[填入]`
```

---

## Phase 1 Sprint 總覽

| Sprint | 標題 | 範圍 | 前置 Sprint |
|--------|------|------|-------------|
| [S01](sprints/S01.md) | Infrastructure Foundation | requirements.txt, docker-compose.yml, .env.example, .gitignore, constants.py, schema.sql, connection.py | — |
| [S02](sprints/S02.md) | Data Layer | models/schemas.py, services/*.py (6 files) | S01 |
| [S03](sprints/S03.md) | Core Pages | pages/work_log.py, pages/project.py, components/sidebar.py | S02 |
| [S04](sprints/S04.md) | Supporting Pages | pages/annual_plan.py, pages/crm.py, pages/sales_plan.py | S02 |
| [S05](sprints/S05.md) | Dashboard & Settings | pages/pipeline.py, pages/settings.py | S03, S04 |
| [S06](sprints/S06.md) | Integration & Polish | app.py, database/seed.py, end-to-end verification | S05 |
| [S07](sprints/S07.md) | Customer Feedback Sprint | CRM 欄位重構（champion→champions, DM 結構, data_year） | S06 |
| [S08](sprints/S08.md) | Navigation Restructuring | 分組側邊欄, presale/postsale 分離, post_closure 頁面 | S07 |
| [S09](sprints/S09.md) | Work Log Split + Postsale Detail | 工作日誌分頁, postsale_detail (task CRUD/Gantt/Burndown) | S08 |
| [S10](sprints/S10.md) | DB Normalization (Contact) | contact + account_contact 正規化 | S09 |
| [S11](sprints/S11.md) | 階段機率 + Deal-Contact + 售前詳情頁 | stage_probability, project_contact, presale_detail | S10 |
| [S12](sprints/S12.md) | 活動時間軸 + 售前任務 + 下一步行動 | due_date, is_next_action, 今日待辦提醒 | S11 |
| [S13](sprints/S13.md) | 全域搜尋 + Visual Board | search_all(), 售前看板 (kanban.py) | S12 |
| [S14](sprints/S14.md) | 客戶層級活動記錄 | work_log nullable project_id + client_id FK | S13 |
| [S15](sprints/S15.md) | 客戶營收彙總 + JSONB 退場 | get_summary_by_client(), JSONB 雙寫退場 | S14 |
| [S16](sprints/S16.md) | 客戶健康分數 + 聯絡人去重 | client_health.py, contact UNIQUE INDEX | S15 |

```
S01 → S02 → S03 ─┐
            └ S04 ─┤→ S05 → S06 → S07 → S08 → S09 → S10 → S11 → S12 → S13 → S14 → S15 → S16
```

> **備註**: S03 與 S04 可平行進行（皆僅依賴 S02）。S07 起為線性依賴。S14-S16 為客戶回饋改進。

---

## 使用方式

1. 開始新 Sprint 前，打開對應的 Sprint 文件
2. 確認 Stage 1 的 User Stories 與 DoD
3. 將 Context Files 列出的檔案餵給 AI
4. 按照五階段流程執行（Stage 0 Kickoff → Stage 1 Planning → Stage 2 Vibe Coding → Stage 3 Review → Stage 4 Retro & Refactor）
5. 完成後更新 Sprint 文件狀態為 `completed`
6. 進入下一個 Sprint
