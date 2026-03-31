# Requirement: Audio Transcription → Intel

**Feature:** `audio-transcription`
**Date:** 2026-03-31
**Status:** Draft

---

## Background

業務人員外出拜訪後回到辦公室，有會議錄音（iPhone Voice Memos .m4a 或 Mac 錄音 .m4a/.mp3）。
目前需要手動聆聽、手動輸入 Intel。
目標：上傳音檔 → Whisper 轉逐字稿 → AI 解析填入 Intel，減少重複作業。

---

## User Stories

### US-1: 上傳音檔

**As a** 業務人員
**I want to** 在 Intel 建立頁或 Intel 詳情頁上傳音檔
**So that** 系統自動轉成逐字稿，不需要手動打字

**Acceptance Criteria:**
- [ ] 支援檔案格式：`.m4a`、`.mp3`、`.mp4`、`.wav`
- [ ] 單檔大小限制 ≤ 25 MB（Whisper API 上限）
- [ ] 超過 25 MB 時顯示錯誤訊息：「檔案過大，請壓縮後再試（上限 25 MB）」
- [ ] 不支援格式時顯示：「不支援此格式，請上傳 m4a / mp3 / mp4 / wav」
- [ ] 上傳中顯示進度狀態（Uploading → Transcribing → Done）
- [ ] 同一 Intel 可重新上傳（覆蓋舊逐字稿）

---

### US-2: 檢視逐字稿

**As a** 業務人員
**I want to** 上傳後看到完整逐字稿文字
**So that** 確認轉錄正確後再送出解析

**Acceptance Criteria:**
- [ ] 逐字稿顯示在 Intel 詳情頁的「原始輸入」區塊（自動填入 `raw_input`）
- [ ] 中英夾雜正確辨識（Whisper 自動偵測語言）
- [ ] 使用者可在送出前直接編輯逐字稿文字
- [ ] 逐字稿超過 3000 字時顯示截斷提示，並提供「全文」展開按鈕
- [ ] 若 Whisper 轉錄失敗，顯示錯誤訊息，保留手動輸入選項

---

### US-3: 自動解析 Intel

**As a** 業務人員
**I want to** 逐字稿產生後自動觸發 Intel AI 解析
**So that** 客戶名稱、痛點、預算等欄位自動填好，我只需要確認

**Acceptance Criteria:**
- [ ] 轉錄完成後自動呼叫 `/intel/{id}/parse`（與手動輸入後的行為一致）
- [ ] AI 解析結果顯示在右側面板（現有 parse 流程）
- [ ] 使用者可修改 AI 解析欄位後再 Confirm
- [ ] 若 AI 解析失敗，逐字稿仍保留在 `raw_input`，使用者可手動送出解析

---

### US-4: 轉錄進度追蹤

**As a** 業務人員
**I want to** 看到轉錄進度（因為可能需要幾十秒）
**So that** 不會以為系統當掉

**Acceptance Criteria:**
- [ ] 上傳後立即顯示狀態列：`上傳中 → 轉錄中 → 解析中 → 完成`
- [ ] 每個階段有對應 icon / spinner
- [ ] 轉錄超過 60 秒顯示提示：「錄音較長，請稍候...」
- [ ] 失敗時顯示哪個階段出錯，並提供 Retry 按鈕

---

## Scope Boundary

| In Scope | Out of Scope |
|----------|-------------|
| 上傳音檔至後端（FastAPI） | 即時錄音（browser mic） |
| Whisper API 轉逐字稿 | 說話人辨識（Speaker Diarization） |
| 中英夾雜辨識 | 自動加標點以外的格式化 |
| 逐字稿填入 Intel `raw_input` | 多段音檔自動合併 |
| 觸發現有 AI Intel 解析流程 | 視訊檔案（>25MB 的 .mp4） |
| 上傳進度狀態顯示 | 逐字稿搜尋 / 時間戳對齊 |
| 25 MB 大小限制與格式驗證 | 離線轉錄（本機 Whisper） |

---

## Technical Notes

- **Transcription API:** OpenAI Whisper API (`/v1/audio/transcriptions`)
- **語言設定:** `language` 不指定（auto-detect），或設為 `zh`（中文優先）
- **後端新增端點:** `POST /api/nexus/intel/{id}/transcribe`
- **前端整合點:** Intel 詳情頁 → 「原始輸入」區塊旁新增上傳按鈕
- **相依服務:** 需 `OPENAI_API_KEY` 環境變數（或用現有 ai_provider 擴充）
