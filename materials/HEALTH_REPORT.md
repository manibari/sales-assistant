---
generated: 2026-07-26
total_subsidies: 55
total_case_studies: 2
total_solutions: 3
---

# Materials Health Report

> Generated: 2026-07-26 (manual run via /material-health)

## Summary

| Check | Status | Issues |
|-------|--------|--------|
| Case study frontmatter | ✅ pass | 0 issues |
| Expired subsidies | ✅ pass | 0 to archive |
| Company info staleness | ⚠️ warn | 5 files stale (132 days), 4 still hold TODO placeholders |
| INDEX consistency | ✅ pass | 0 mismatches |
| Orphaned files | ✅ pass | 0 orphans |

## Details

### Case Studies (2 files)

Frontmatter 完整性：兩份案例的必填欄位（client / industry / solution_type / year / outcome）皆齊全。

⚠️ 內容品質備註（非 frontmatter 問題，延續自 2026-07-12 起的報告）：兩份案例的內文仍是模板佔位狀態 —
- `chimei-foods_2025.md` — L16 客戶背景章節仍為 `<!-- TODO: 填入客戶背景描述 -->`
- `example-tech_2025.md` — 同上，且「範例科技」為示範資料，建議確認是否保留

### Subsidies (55 active / 31 archived)

- 到期檢查：以 2026-07-26 為基準，**0 件過期** — 上週報告的航太產業 AERO 輔導計畫（7/17 截止）已移入 `programs/archived/` 並自 INDEX 移除。✅ 已解決
- 55 件 `status: active` 且 deadline 未過（或為長期/隨到隨審），狀態一致。
- `programs/archived/` 31 件無異常。
- 近期截止（30 天內），提案時優先引用：
  - 關鍵醫材國產量能自主整合補助計畫（115年度） — **2026-07-31（剩 5 天）**
- INDEX 產生於 2026-07-23（subsidy-scraper），與檔案系統同步。

### Company Info (5 files)

全部 5 檔最後修改日為 **2026-03-16**，距今 **132 天**，超過 90 天門檻：

| 檔案 | 天數 | TODO 佔位 |
|------|------|-----------|
| `company/profile.md` | 132 | ⚠️ `<!-- TODO: 請填入實際公司資訊 -->` |
| `company/capabilities.md` | 132 | — |
| `company/methodology.md` | 132 | ⚠️ `<!-- TODO: 請填入實際方法論 -->` |
| `company/differentiators.md` | 132 | ⚠️ `<!-- TODO: 請填入實際差異化優勢 -->` |
| `company/team.md` | 132 | ⚠️ `<!-- TODO: 請填入實際團隊資訊 -->` |

此項自 2026-07-12 報告（118 天）起持續惡化 — 建議安排一次 company/ 內容補齊，否則 sales-material 組裝提案時會引用佔位文字。

### INDEX Mismatches

- `case-studies/INDEX.md` — 2/2 檔案皆列出，無缺漏。✅
- `solutions/INDEX.md` — 3/3 檔案（ai-data ×2、consulting ×1）皆列出；`saas/` 目錄尚未建立，INDEX 中標記「待新增」，一致。✅
- `subsidies/INDEX.md` — 標頭宣稱 55 件，`programs/*.md` 實際 55 件，逐檔比對（INDEX 連結 vs 目錄，雙向 comm 比對）皆無差異、無重複連結。✅

### Orphaned Files

無孤兒檔案 — 所有 case-studies 與 solutions 的 .md 均被對應 INDEX 引用。✅
