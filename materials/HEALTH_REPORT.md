---
generated: 2026-11-01
total_subsidies: 58
total_archived_subsidies: 41
total_case_studies: 2
total_solutions: 3
---

# Materials Health Report

> Generated: 2026-11-01 (via /sales-material-health)

## Summary

| Check | Status | Issues |
|-------|--------|--------|
| Case study frontmatter | ✅ pass | 0 issues（必填欄位齊全；內文 TODO 佔位另計） |
| Expired subsidies | ⚠️ warn | 4 to archive（截止日 2026-10-30） |
| Company info staleness | ⚠️ warn | 5 stale files（230 天），4 份仍是 TODO 佔位 |
| INDEX consistency | ✅ pass | 0 mismatches（補助 58/58、案例 2/2、方案 3/3） |
| Orphaned files | ✅ pass | 0 orphans（無死連結） |

## Details

### Case Studies

必填欄位（client / industry / solution_type / year / outcome）兩份皆齊全，`year` 皆為數字。

內容層面待補（不影響 frontmatter 檢查）：

- `chimei-foods_2025.md` — L16 `<!-- TODO: 填入客戶背景描述 -->`，規模、主要產品欄位空白
- `example-tech_2025.md` — L16 同上；客戶名「範例科技」為範例資料，非真實案例

> 案例庫目前只有 1 份可能為真實案例，提案素材配對能力有限。

### Subsidies

**應歸檔（deadline < 2026-11-01，status 仍為 active）：**

| 檔案 | 截止日 |
|------|--------|
| `programs/臺法創新研發合作補助計畫-115年度.md` | 2026-10-30 |
| `programs/補助廠商分散及開拓海外市場.md` | 2026-10-30 |
| `programs/關鍵礦物應用高值化推動計畫-115年度.md` | 2026-10-30 |
| `programs/雲市集工業館-AI工具庫點數補助計畫-115年度.md` | 2026-10-30 |

連帶影響：`subsidies/INDEX.md` 及 `by-industry/`（all-industries / manufacturing / retail / technology）仍列出這 4 件。下次 `/gov-subsidy-scraper` 執行時應會自動歸檔並重建索引；若要立即處理可手動跑一次 scraper。

**狀態不一致：** 0 件（programs/ 下全部 `status: active`）。

**即將截止（60 天內）：**

- 2026-12-07 — SBIR 企業跨域研發補助（116年度）
- 2026-12-20 — 服務業AI人才培育
- 2026-12-31 — 航港產業數位轉型成果獎勵方案、企業創新研發布局推動計畫、TAIWAN SELECT 食品品牌、研發轉型支持計畫個案補助、新創賦能中小企業升級轉型、補助中小用戶導入節能服務

### Company Info

5 份檔案最後修改日皆為 2026-03-16（230 天，超過 90 天門檻）：

| 檔案 | 狀態 |
|------|------|
| `profile.md` | 超過 90 天未更新 + 尚未填入（L3 TODO） |
| `team.md` | 超過 90 天未更新 + 尚未填入（L3 TODO） |
| `methodology.md` | 超過 90 天未更新 + 尚未填入（L3 TODO） |
| `differentiators.md` | 超過 90 天未更新 + 尚未填入（L3 TODO） |
| `capabilities.md` | 超過 90 天未更新（無 TODO） |

> 此問題已連續多週出現。公司基本資料是所有提案的底稿，建議優先補齊 profile / team（需區分正傑科技與詠鋐智能兩個身分）。

### INDEX Mismatches

- `case-studies/INDEX.md`：列 2 件，目錄 2 件 ✅
- `solutions/INDEX.md`：列 3 件，子目錄 3 件 ✅（`saas/` 目錄不存在，INDEX 中 SaaS 區塊為「待新增」佔位）
- `subsidies/INDEX.md`：宣稱 58 件、連結 58 件、`programs/*.md` 58 件 ✅

### Orphaned Files

無。所有案例與方案檔皆被 INDEX 引用，INDEX 內無指向不存在檔案的連結。
