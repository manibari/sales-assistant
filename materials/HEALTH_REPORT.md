---
generated: 2026-07-12
total_subsidies: 56
total_case_studies: 2
total_solutions: 3
---

# Materials Health Report

> Generated: 2026-07-12 09:00 (manual run via /material-health)

## Summary

| Check | Status | Issues |
|-------|--------|--------|
| Case study frontmatter | ✅ pass | 0 issues |
| Expired subsidies | ✅ pass | 0 to archive |
| Company info staleness | ⚠️ warn | 5 files stale (118 days), 4 still hold TODO placeholders |
| INDEX consistency | ✅ pass | 0 mismatches |
| Orphaned files | ✅ pass | 0 orphans (1 iCloud conflict dupe removed) |

## Details

### Case Studies (2 files)

Frontmatter 完整性：兩份案例的必填欄位（client / industry / solution_type / year / outcome）皆齊全。

⚠️ 內容品質備註（非 frontmatter 問題）：兩份案例的內文仍是模板佔位狀態 —
- `chimei-foods_2025.md` — 客戶背景 / 挑戰 / 方案架構 / 客戶證言皆為 TODO 或空白
- `example-tech_2025.md` — 同上，且「範例科技」為示範資料，建議確認是否保留

### Subsidies (56 active / 30 archived)

- 到期檢查：以 2026-07-12 為基準，**0 件已過期**。全部 56 件 `status: active`，與 `programs/` 位置一致。
- `programs/archived/` 30 件均無 `status: active` 殘留，狀態一致。
- 近期截止（30 天內），提案時優先引用：
  - 航太產業AERO輔導計畫（115年度） — **2026-07-17（剩 5 天）**
  - 關鍵醫材國產量能自主整合補助計畫（115年度） — **2026-07-31（剩 19 天）**
- INDEX 產生於 2026-07-09（subsidy-scraper），資料新鮮。

### Company Info (5 files) ⚠️

全部 5 檔最後修改日為 **2026-03-16（118 天前，超過 90 天門檻）**：

| 檔案 | 過期 | TODO 佔位 |
|------|------|-----------|
| profile.md | ⚠️ 118 天 | ⚠️ `<!-- TODO: 請填入實際公司資訊 -->` |
| capabilities.md | ⚠️ 118 天 | — |
| team.md | ⚠️ 118 天 | ⚠️ `<!-- TODO: 請填入實際團隊資訊 -->` |
| methodology.md | ⚠️ 118 天 | ⚠️ `<!-- TODO: 請填入實際方法論 -->` |
| differentiators.md | ⚠️ 118 天 | ⚠️ `<!-- TODO: 請填入實際差異化優勢 -->` |

> 此項自 2026-07-05 上次健檢即為 warn，持續未處理。公司資料是所有 sales deck 的素材源頭，建議優先補齊（正傑科技 / 詠鋐智能 雙公司脈絡）。

### INDEX Consistency

| INDEX | 目錄實際 | INDEX 記載 | 結果 |
|-------|----------|-----------|------|
| case-studies/INDEX.md | 2 檔 | 2 筆 | ✅ |
| solutions/INDEX.md | 3 檔（ai-data ×2, consulting ×1） | 3 筆 | ✅ |
| subsidies/INDEX.md | programs/ 56 檔 | 56 筆（自報 56 件） | ✅ |

備註：`solutions/saas/` 目錄為空，INDEX 中為「待新增」佔位 — 一致，非錯誤。

### Orphaned Files

- case-studies / solutions：無未列入 INDEX 的 .md 檔。
- 已清理：`HEALTH_REPORT 2.md`（2026-03-18 的 iCloud 衝突副本，較正本舊，經 mtime 比對後刪除）。
- 觀察（不計入 orphan）：`clients/` 與 `subsidies/` 內累積大量 scraper 的 `.jsonl` / `.log` 日常產出檔（clients 237 檔、subsidies 168 檔中多數為此類）；`tenders/` 有 3,547 檔。不影響素材健康，但若要控制 repo 體積可考慮定期歸檔或加入 .gitignore。

## Action Items

1. **（重複警告）補齊 `company/` 5 檔** — 118 天未更新且 4 檔仍是 TODO 模板，是目前素材庫最大缺口。
2. 兩份案例（奇美食品、範例科技）內文仍為模板骨架，接到真實提案前建議至少完成一份完整案例。
3. 航太 AERO（07-17）、關鍵醫材（07-31）兩件補助即將截止，如有相關客戶請於本週引用。
