---
generated: 2026-10-25
total_subsidies: 58
total_archived_subsidies: 41
total_case_studies: 2
total_solutions: 3
---

# Materials Health Report

> Generated: 2026-10-25 (via /sales-material-health)

## Summary

| Check | Status | Issues |
|-------|--------|--------|
| Case study frontmatter | ✅ pass | 0 issues（必填欄位齊全；內文 TODO 佔位另計） |
| Expired subsidies | ✅ pass | 0 to archive（4 件 5 天後截止） |
| Company info staleness | ⚠️ warn | 5 stale files（223 天），4 份仍是 TODO 佔位 |
| INDEX consistency | ✅ pass | 0 mismatches（58/58、2/2、3/3） |
| Orphaned files | ✅ pass | 0 orphans |
| Frontmatter 格式 | ✅ pass | archived YAML 未關閉問題已修（上次 8 件 → 0） |

與上一份報告（09-27）相比：過期補助已歸檔（active 61 → 58，archived 37 → 41）；8 個 archived 檔的 YAML 已修好。公司資訊仍是唯一的實質缺口。

⚠️ **10-04、10-11、10-18 三週的排程都沒產出報告**：前兩次撞到 weekly usage limit，10-18 是網路 / DNS 失敗（`ENOTFOUND`）。所以這份是隔了 4 週的第一份。stderr 都是空的，失敗只記在 `health-2026-MM-DD.jsonl` 的 result 行裡——runner 沒有把失敗暴露出來。

---

## 本週該動手的三件事

1. **10-30（剩 5 天）4 件同日截止** — 臺法創新研發合作、關鍵礦物應用高值化、雲市集工業館·AI 工具庫點數、補助廠商分散及開拓海外市場。要投就這週決定。
2. **填公司資訊** — `company/` 4 份仍是 TODO，已掛 223 天。`sales-material` 組提案時「我們是誰 / 差異化 / 團隊 / 方法論」四段沒有內容可抓。先決定是單一公司還是分 正傑科技 / 詠鋐智能 兩份。
3. **讓 headless 失敗會被看見** — `scripts/sales-material-health.sh` 在 Claude 回傳錯誤時，stderr 仍是空的、也沒有任何通知。建議在 runner 裡檢查 result 行（如 `is_error`）並送 Telegram 通知。

---

## Details

### Case Studies

必填欄位（client / industry / solution_type / year / outcome）**兩個檔案全部齊全**，year 皆為數字：

| 檔案 | client | industry | solution_type | year | outcome |
|------|--------|----------|---------------|------|---------|
| chimei-foods_2025.md | 奇美食品 | 食品製造 | 數位轉型, 供應鏈管理 | 2025 | 品質異常反應時間縮短 60% |
| example-tech_2025.md | 範例科技 | 科技業 | AI 預測維護 | 2025 | 設備停機時間減少 40% |

⚠️ 內容層面（不算 frontmatter 失敗）：

- `example-tech_2025.md` 的「範例科技」是示範資料，真實案例只有 1 則。
- 兩個檔案第 16 行都還有 `<!-- TODO: 填入客戶背景描述 -->`。

### Subsidies

**0 件應歸檔**：`programs/` 內 58 件，沒有 deadline < 2026-10-25 的檔案。

**狀態一致性**：58 件全為 `status: active`，無不一致。41 件 `deadline` 為空，全都有 `deadline_text`（長期／隨到隨審）。

14 天內截止：

| 截止日 | 剩餘 | 計畫 |
|--------|------|------|
| 2026-10-30 | **5 天** | 臺法創新研發合作補助計畫（115年度） |
| 2026-10-30 | **5 天** | 關鍵礦物應用高值化推動計畫（115年度） |
| 2026-10-30 | **5 天** | 雲市集工業館 — AI 工具庫點數補助計畫（115年度） |
| 2026-10-30 | **5 天** | 補助廠商分散及開拓海外市場 |

再往後：SBIR 企業跨域研發（116 年度）12-07、服務業 AI 人才培育 12-20、另有 6 件 12-31 截止。

### Company Info

**5 個檔案全部超過 90 天門檻**（mtime 均為 2026-03-16，**223 天**未更新）：

| 檔案 | 未更新天數 | TODO 佔位 |
|------|-----------|-----------|
| profile.md | 223 | ⚠️ `<!-- TODO: 請填入實際公司資訊 -->` |
| differentiators.md | 223 | ⚠️ `<!-- TODO: 請填入實際差異化優勢 -->` |
| team.md | 223 | ⚠️ `<!-- TODO: 請填入實際團隊資訊 -->` |
| methodology.md | 223 | ⚠️ `<!-- TODO: 請填入實際方法論 -->` |
| capabilities.md | 223 | — |

### INDEX Mismatches

**全部一致，0 mismatch。**

| INDEX | 宣告 | 磁碟實際 | 結果 |
|-------|------|---------|------|
| subsidies/INDEX.md | 58 件 active（10-22 產生） | 58 個 `programs/*.md` | ✅ 雙向比對 0 落差 |
| case-studies/INDEX.md | 2 則 | 2 個 `.md` | ✅ 連結皆有效 |
| solutions/INDEX.md | 3 個方案 | 3 個 `.md`（ai-data×2, consulting×1） | ✅ 連結皆有效 |

小提醒（非錯誤）：`solutions/INDEX.md` 列有 `saas/` 分類但磁碟上無此目錄，屬已知待辦。

### Orphaned Files

**0 orphans。** case-studies、solutions、subsidies/programs 的每個 `.md` 都被對應 INDEX 引用。

### Frontmatter 格式

`programs/archived/` 41 件全部能正常解析（開頭 `---` 與結尾 `---` 都在）。上次報告的 `status: expired---` 黏行問題，現在 `grep -l 'expired---'` 結果為 0。

### 資料品質觀察（非 skill 定義的檢查項）

`programs/*.md` 有 **18 件**的 `agency` 欄位被爬蟲灌入整段聯絡資訊（「主辦單位…執行單位…聯絡窗口…email／電話」），連帶撐爆 `subsidies/INDEX.md` 的「主辦機關」欄。例如：補助中小用戶導入節能服務、補助廠商分散及開拓海外市場、提供 30 人以下的中小微企業優惠貸款。建議 scraper 的 `agency` 只取主辦機關名稱，或加長度上限。
