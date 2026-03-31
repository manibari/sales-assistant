# User Flow: Audio Transcription → Intel

**Feature:** `audio-transcription`
**Date:** 2026-03-31
**Related Requirement:** `docs/requirements/audio-transcription.md`

---

## Entry Points

| Entry | Where | Trigger |
|-------|-------|---------|
| A | Intel 詳情頁（已存在的 Intel） | 點擊「上傳錄音」按鈕 |
| B | 新增 Intel 頁 | 選擇「上傳音檔」建立方式 |

---

## Happy Path Flow

```mermaid
flowchart TD
    START([業務人員回到辦公室]) --> ENTRY{從哪裡進入？}

    ENTRY -->|已有 Intel 草稿| DETAIL[Intel 詳情頁\n/intel/:id]
    ENTRY -->|全新建立| CREATE[新增 Intel 頁\n/intel/new]

    CREATE -->|選擇「上傳音檔」| UPLOAD_ZONE[顯示上傳區塊]
    DETAIL -->|點擊「上傳錄音」按鈕| UPLOAD_ZONE

    UPLOAD_ZONE -->|拖曳或點選檔案| FILE_PICK[選擇音檔\n.m4a / .mp3 / .mp4 / .wav]

    FILE_PICK --> VALIDATE{前端驗證}
    VALIDATE -->|格式不支援| ERR_FORMAT[錯誤提示：不支援格式\n保留上傳區塊]
    VALIDATE -->|檔案 > 25MB| ERR_SIZE[錯誤提示：檔案過大\n保留上傳區塊]
    VALIDATE -->|通過| UPLOADING[狀態：上傳中 ⟳]
    ERR_FORMAT --> FILE_PICK
    ERR_SIZE --> FILE_PICK

    UPLOADING -->|POST /intel/:id/transcribe| API_UPLOAD{後端接收}
    API_UPLOAD -->|網路錯誤| ERR_NETWORK[錯誤：上傳失敗\nRetry 按鈕]
    ERR_NETWORK -->|Retry| UPLOADING
    API_UPLOAD -->|成功| TRANSCRIBING[狀態：轉錄中 ⟳\nWhisper API 處理]

    TRANSCRIBING -->|> 60 秒| SLOW_HINT[提示：錄音較長，請稍候...]
    SLOW_HINT --> TRANSCRIBING
    TRANSCRIBING -->|Whisper 失敗| ERR_WHISPER[錯誤：轉錄失敗\n顯示失敗階段 + Retry]
    ERR_WHISPER -->|Retry| TRANSCRIBING
    TRANSCRIBING -->|轉錄完成| TRANSCRIPT_READY[逐字稿填入 raw_input\n顯示文字內容]

    TRANSCRIPT_READY --> REVIEW{使用者確認逐字稿}
    REVIEW -->|直接送出| PARSING[狀態：解析中 ⟳\nPOST /intel/:id/parse]
    REVIEW -->|編輯後送出| EDIT_TRANSCRIPT[編輯逐字稿文字] --> PARSING

    PARSING -->|AI 解析失敗| ERR_PARSE[錯誤：解析失敗\n逐字稿保留，可手動送出]
    ERR_PARSE -->|手動送出| PARSING
    PARSING -->|解析成功| PARSED_RESULT[狀態：完成 ✓\n右側面板顯示 AI 解析欄位]

    PARSED_RESULT --> CONFIRM{使用者確認 Intel}
    CONFIRM -->|修改欄位| EDIT_FIELDS[編輯 AI 解析結果] --> CONFIRM
    CONFIRM -->|Confirm| DONE((Intel 已建立\n狀態 confirmed))
```

---

## Error Branch Summary

| 錯誤情境 | 發生階段 | 處理方式 |
|----------|----------|----------|
| 格式不支援 | 前端驗證 | 紅色提示，重新選檔 |
| 檔案 > 25MB | 前端驗證 | 紅色提示，重新選檔 |
| 網路上傳失敗 | 上傳中 | 顯示 Retry 按鈕 |
| Whisper API 失敗 | 轉錄中 | 顯示失敗階段 + Retry |
| AI Parse 失敗 | 解析中 | 逐字稿保留，可手動觸發解析 |

---

## Screen Inventory

| # | Screen | Purpose | Key Elements |
|---|--------|---------|-------------|
| S1 | Intel 詳情頁（含上傳區塊） | 主要入口，對已有草稿的 Intel 上傳錄音 | 上傳按鈕、狀態列、逐字稿文字框、AI 解析面板 |
| S2 | 新增 Intel 頁（音檔模式） | 全新建立，選擇音檔作為輸入來源 | 輸入方式切換、拖曳上傳區、狀態列 |
| S3 | 上傳進度狀態列 | 跨三階段顯示進度 | 上傳中 / 轉錄中 / 解析中 / 完成，含 spinner 與錯誤態 |
| S4 | 逐字稿預覽區 | 顯示 Whisper 結果，允許編輯 | 可編輯 textarea、字數提示、「展開全文」按鈕（>3000字） |
| S5 | 錯誤提示 + Retry | 任一階段失敗時顯示 | 失敗階段標示、錯誤訊息、Retry 按鈕 |
