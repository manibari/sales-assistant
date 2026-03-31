# Task Plan: Audio Transcription → Intel

**Goal:** 業務可上傳音檔 (.m4a/.mp3/.mp4/.wav)，後端用 Whisper API 轉逐字稿，自動填入 Intel raw_input 並觸發 AI 解析。

**Requirements:** `docs/requirements/audio-transcription.md`
**Flow:** `docs/flows/audio-transcription-flow.md`
**Mockup:** `mockups/audio-transcription.html`
**Date:** 2026-03-31

---

## Codebase Context

| 項目 | 位置 |
|------|------|
| Intel 後端 router | `backend/routers/nexus/intel.py` (prefix: `/api/nx/intel`) |
| AI 服務層 | `services/nexus/ai/` (新架構：非對話式 AI 放這裡) |
| Frontend Intel 頁 | `frontend/src/app/intel/page.tsx` (~800 行) |
| Frontend API client | `frontend/src/lib/nexus-api.ts` |
| openai SDK | ✅ 已在 requirements.txt |
| Parse 流程 | `POST /api/nx/intel/{id}/parse` → `intel_ai.parse_raw_intel()` |

**關鍵觀察：**
- `intel/page.tsx` 已有 `Mic` icon import，但未接功能 → 改成上傳觸發點
- 上傳後需更新 `intel.raw_input`（`PATCH /{id}`），再呼叫 `/parse`
- Whisper API 端點：`openai.audio.transcriptions.create()`，需 `OPENAI_API_KEY`

---

## Phases

### Phase 1: 後端 AI 服務層 [ ]
**File:** `services/nexus/ai/transcription_ai.py`

- [ ] T1.1 新建 `transcription_ai.py`
  - `transcribe_audio(file_bytes: bytes, filename: str) -> str`
  - 呼叫 `openai.audio.transcriptions.create(model="whisper-1", file=...)`
  - 不指定語言（auto-detect 中英文）
  - 失敗拋出 `RuntimeError` with 清楚訊息

### Phase 2: 後端 API 端點 [ ]
**File:** `backend/routers/nexus/intel.py`

- [ ] T2.1 新增 `POST /{intel_id}/transcribe` 端點
  - 接受 `UploadFile`（multipart form）
  - 前端驗證備援：格式白名單 `{.m4a, .mp3, .mp4, .wav}`、大小 ≤ 25MB
  - 呼叫 `transcription_ai.transcribe_audio()`
  - 呼叫 `update_intel(intel_id, raw_input=transcript)`
  - 呼叫 `intel_ai.parse_raw_intel(transcript)` → parsed
  - 呼叫 `update_intel(intel_id, parsed_json=...)`
  - 回傳 `{transcript, parsed, ai_reply}`（ai_reply 暫為空字串，由前端決定是否再呼叫 chat）
  - 加入 check_ai_available guard（503）
  - 加入 check_openai_available guard（503，單獨判斷）

### Phase 3: 前端 API Client [ ]
**File:** `frontend/src/lib/nexus-api.ts`

- [ ] T3.1 在 `nxApi.intel` 加入 `transcribe(id, file: File)` 方法
  - 用 `FormData` 送出
  - 回傳 `{transcript: string, parsed: object, ai_reply: string}`

### Phase 4: 前端 UI [ ]
**File:** `frontend/src/app/intel/page.tsx`

- [ ] T4.1 新增上傳狀態 state
  ```ts
  type TranscribeStage = 'idle' | 'uploading' | 'transcribing' | 'parsing' | 'done' | 'error'
  const [transcribeStage, setTranscribeStage] = useState<TranscribeStage>('idle')
  const [transcribeError, setTranscribeError] = useState<string | null>(null)
  ```
- [ ] T4.2 改造 `Mic` icon 按鈕 → 觸發隱藏的 `<input type="file" accept=".m4a,.mp3,.mp4,.wav">`
- [ ] T4.3 前端格式/大小驗證（25MB、副檔名）
- [ ] T4.4 `handleAudioUpload(file: File)` 函式
  - 依序設定 stage: uploading → transcribing（給 UX 感知）
  - 呼叫 `nxApi.intel.transcribe(intelId, file)`
  - 成功：把逐字稿加入 messages（role: user）、更新 parsed、設 stage: done
  - 失敗：設 stage: error，記錄 error message
- [ ] T4.5 進度狀態列 UI component（inline）
  - 4 個 step badge：上傳 / 轉錄 / 解析 / 完成
  - 各 step 有 spinner / check / error icon
  - 超過 8 秒顯示「錄音較長，請稍候...」提示
- [ ] T4.6 錯誤 UI：顯示 transcribeError + Retry 按鈕

### Phase 5: 環境設定文件 [ ]
- [ ] T5.1 在 `.env.example` 加入 `OPENAI_API_KEY=` 註解說明
- [ ] T5.2 確認 Whisper 不需要額外 pip 套件（openai SDK 已含）

---

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| — | — | — |

---

## Key Decisions
- Whisper model: `whisper-1`（唯一可用的 transcription model）
- 語言: auto-detect（不傳 language 參數），讓 Whisper 自動處理中英夾雜
- 後端端點放在 intel router（不是 documents router），因為它直接操作 intel 的 raw_input
- 前端：利用已有的 Mic icon 作為觸發點，不新增按鈕
- 逐字稿在前端以 user message 形式顯示，維持現有 chat UX

---

## Files to Create/Modify

| 檔案 | 動作 |
|------|------|
| `services/nexus/ai/transcription_ai.py` | 新建 |
| `backend/routers/nexus/intel.py` | 修改（加 transcribe endpoint） |
| `frontend/src/lib/nexus-api.ts` | 修改（加 transcribe method） |
| `frontend/src/app/intel/page.tsx` | 修改（加 upload UI + handler） |
| `.env.example` | 修改（加 OPENAI_API_KEY 說明） |
