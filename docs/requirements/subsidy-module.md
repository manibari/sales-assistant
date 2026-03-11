# Requirement: 補助案獨立模組

## Overview

| Item | Detail |
|------|--------|
| **Target User** | B2B 銷售人員（使用者自己） |
| **Problem** | 政府補助案資訊散落在情報中，無法獨立追蹤進度、配對客戶、管理申請流程 |
| **Trigger** | Telegram Bot 已能分類 `role="subsidy"` 情報，但無法結構化管理補助案生命週期 |
| **Module Type** | 獨立模組，與商機/情報/日曆平行 |

## 核心資料欄位

| 欄位 | 說明 | 類型 |
|------|------|------|
| 來源 | 補助案來源管道 | text |
| 主辦機關 | 負責機構 (e.g. 經濟部、工業局) | text |
| 大類 | 計畫分類 (SBIR/SIIR/地方型/其他) | enum |
| 計畫名稱 | 補助計畫全名 | text (required) |
| 申請資格 | 資格條件說明 | text |
| 補助額度 | 補助金額或範圍 | text |
| 申請範疇 | 可申請的技術/產業領域 | text |
| 申請文件 | 需要準備的文件清單 | text |
| 申請截止 | 截止日期 | date |
| 資料來源 | 原始資料連結/出處 | url/text |

## User Stories

### US-1: 建立補助案記錄

**As a** 銷售人員
**I want to** 手動建立一筆補助案記錄，填入計畫名稱、主辦機關、截止日期等資訊
**So that** 我可以集中管理所有追蹤中的補助案機會

**Acceptance Criteria:**
- [ ] Given 在補助案列表頁，when 點擊「新增」，then 進入新增頁面
- [ ] Given 新增頁面，when 填入計畫名稱（必填）+ 其他欄位後送出，then 建立記錄並導向詳情頁
- [ ] Given 新增頁面，when 未填計畫名稱就送出，then 顯示必填提示

### US-2: 瀏覽補助案列表

**As a** 銷售人員
**I want to** 查看所有補助案，可按階段或截止日排序
**So that** 我能快速找到需要處理的補助案

**Acceptance Criteria:**
- [ ] Given 補助案列表頁，when 切換「階段」view，then 補助案按階段分組顯示
- [ ] Given 補助案列表頁，when 切換「截止日」view，then 按截止日由近到遠排序
- [ ] Given 列表中有已關閉的補助案，when 預設顯示，then 只顯示 active 狀態
- [ ] Given 有即將到期（<30天）的補助案，when 顯示，then 有視覺提示（紅/橘色標記）

### US-3: 編輯補助案詳情

**As a** 銷售人員
**I want to** 在詳情頁 inline 編輯所有欄位
**So that** 我能隨時更新補助案資訊

**Acceptance Criteria:**
- [ ] Given 詳情頁，when 點擊任何可編輯欄位，then 切換為編輯模式
- [ ] Given 編輯模式，when 按 Enter 或點擊確認，then 儲存並刷新
- [ ] Given 編輯模式，when 按 Escape，then 取消編輯
- [ ] Given 階段欄位，when 選擇新階段，then 立即推進並更新 pipeline bar

### US-4: 補助案階段管理

**As a** 銷售人員
**I want to** 推進補助案的階段（草稿→評估中→申請中→審查中→核定/未通過→執行中→結案）
**So that** 我能追蹤每個補助案的進度

**Acceptance Criteria:**
- [ ] Given 詳情頁頂部有 pipeline bar，when 點擊下一個階段，then 推進到該階段
- [ ] Given 補助案在「審查中」，when 結果出來，then 可以選擇「核定」或「未通過」
- [ ] Given 補助案在「未通過」或「結案」，when 查看，then 顯示為已完成狀態

### US-5: 連結商機

**As a** 銷售人員
**I want to** 將補助案連結到一或多個商機
**So that** 我能看到哪些商機可以透過補助案資金推動

**Acceptance Criteria:**
- [ ] Given 詳情頁右側，when 點擊「+ 連結商機」，then 顯示商機選擇器
- [ ] Given 已連結的商機，when 點擊商機名稱，then 導向商機詳情頁
- [ ] Given 已連結的商機，when 想取消連結，then 可以移除
- [ ] Given 商機詳情頁，when 該商機有連結的補助案，then 也應顯示補助案資訊

### US-6: 連結客戶與夥伴

**As a** 銷售人員
**I want to** 將補助案連結到申請客戶和合作夥伴
**So that** 我能知道誰在申請、誰協助

**Acceptance Criteria:**
- [ ] Given 詳情頁，when 設定 client_id，then 顯示客戶名稱並可點擊進入客戶頁
- [ ] Given 詳情頁，when 設定 partner_id，then 顯示夥伴名稱並可點擊進入夥伴頁
- [ ] Given 客戶詳情頁，when 該客戶有關聯補助案，then 顯示在「相關補助案」區塊

### US-7: 情報自動建立補助案

**As a** 銷售人員
**I want to** 透過 Telegram 輸入 role=subsidy 的情報時，確認後自動建立補助案記錄
**So that** 我不需要手動重複輸入資料

**Acceptance Criteria:**
- [ ] Given Telegram 情報 role=subsidy，when /done 確認，then materialize 自動建立 nx_subsidy 記錄
- [ ] Given materialize 成功，when Telegram 回覆，then 顯示「已建立補助案 XXX」
- [ ] Given 已存在同名補助案，when 再次 materialize，then 不重複建立

### US-8: 補助案文件管理

**As a** 銷售人員
**I want to** 在補助案詳情頁上傳或連結相關文件
**So that** 計畫書、核定函等文件集中管理

**Acceptance Criteria:**
- [ ] Given 詳情頁右側，when 點擊「+ 新增文件」，then 開啟 FileUploadModal
- [ ] Given FileUploadModal，when 上傳檔案或貼連結，then 文件關聯到此補助案
- [ ] Given 已有文件，when 顯示列表，then 可點擊下載/開啟

### US-9: 搜尋補助案

**As a** 銷售人員
**I want to** 透過全域搜尋找到補助案
**So that** 我能快速定位特定計畫

**Acceptance Criteria:**
- [ ] Given 全域搜尋列，when 輸入補助案名稱或主辦機關，then 搜尋結果包含補助案
- [ ] Given 搜尋結果，when 點擊補助案，then 導向詳情頁

## Scope Boundary

| In Scope | Out of Scope |
|----------|-------------|
| 補助案 CRUD + 階段管理 | 自動爬取政府網站的補助公告 |
| 連結商機、客戶、夥伴 | AI 自動配對客戶 × 補助案（Engine 2） |
| 情報 materialize 自動建立 | 補助案申請書自動生成 |
| 文件上傳/連結 | 多人協作編輯計畫書 |
| 全域搜尋整合 | 補助案到期自動推播通知 |
| 列表 + 詳情 + 新增頁面 | 統計報表 / 補助案成功率分析 |
| Desktop sidebar 導航 | Mobile bottom nav（低頻使用，暫不加） |
| Dashboard 即將到期 widget | 日曆整合（截止日顯示在月曆上） |
