---
generated: 2026-11-08
total_subsidies: 55
total_archived_subsidies: 44
total_case_studies: 2
total_solutions: 3
---

# Materials Health Report

> Generated: 2026-11-08 (via /sales-material-health)

## Summary

| Check | Status | Issues |
|-------|--------|--------|
| Case study frontmatter | ✅ pass | 0 issues（必填欄位齊全；內文 TODO 佔位另計） |
| Expired subsidies | ✅ pass | 0 to archive（上週 4 件已處理） |
| Company info staleness | ⚠️ warn | 5 stale files（237 天），4 份仍是 TODO 佔位 |
| INDEX consistency | ✅ pass | 0 mismatches（補助 55/55、案例 2/2、方案 3/3） |
| Orphaned files | ✅ pass | 0 orphans（無死連結） |

## Details

### Case Studies

必填欄位（client / industry / solution_type / year / outcome）兩份皆齊全；`solution_type` 為陣列、`year` 為數字。

內容層面待補（不影響 frontmatter 檢查）：

- `chimei-foods_2025.md` — L16 `<!-- TODO: 填入客戶背景描述 -->`
- `example-tech_2025.md` — L16 同上；客戶名「範例科技」為範例資料，非真實案例

> 案例庫實質只有 1 份可能為真實案例，提案素材配對能力有限。

### Subsidies

**應歸檔（deadline < 2026-11-08）：** 0 件。

上週（2026-11-01）報告的 4 件已處理（2026-11-02 scraper refresh）：

| 檔案 | 處理結果 |
|------|----------|
| `臺法創新研發合作補助計畫-115年度.md` | 已移入 `programs/archived/` |
| `補助廠商分散及開拓海外市場.md` | 已移入 `programs/archived/` |
| `關鍵礦物應用高值化推動計畫-115年度.md` | 已移入 `programs/archived/` |
| `雲市集工業館-AI工具庫點數補助計畫-115年度.md` | 仍有效 — 截止日更新為 2027-10-20（116/10/20 前送件） |

**狀態不一致：** 0 件（programs/ 下 55 件全部 `status: active`）。

**無截止日（`deadline: ""`）：** 41 / 55 件。多為常態受理或「洽計畫辦公室」型計畫，無法自動判斷是否過期，僅供參考，非本次 warn 項目。

**即將截止（60 天內）：**

- 2026-12-07 — SBIR 企業跨域研發補助（116年度）
- 2026-12-20 — 服務業AI人才培育
- 2026-12-31 — 航港產業數位轉型成果獎勵方案、企業創新研發布局推動計畫、TAIWAN SELECT 食品品牌、研發轉型支持計畫個案補助、新創賦能中小企業升級轉型、補助中小用戶導入節能服務

### Company Info

5 份檔案最後修改日皆為 2026-03-16（237 天，超過 90 天門檻）：

| 檔案 | 狀態 |
|------|------|
| `profile.md` | 超過 90 天未更新 + 尚未填入（L3 TODO） |
| `team.md` | 超過 90 天未更新 + 尚未填入（L3 TODO） |
| `methodology.md` | 超過 90 天未更新 + 尚未填入（L3 TODO） |
| `differentiators.md` | 超過 90 天未更新 + 尚未填入（L3 TODO） |
| `capabilities.md` | 超過 90 天未更新（無 TODO） |

> 此問題已連續多週出現且是目前唯一的 warn。公司基本資料是所有提案的底稿，建議優先補齊 profile / team（需區分正傑科技與詠鋐智能兩個身分）。

### INDEX Mismatches

- `case-studies/INDEX.md`：表格 + 清單共 4 個連結，對應 2 個檔案，目錄 2 件 ✅
- `solutions/INDEX.md`：列 3 件，子目錄 3 件 ✅（`saas/` 目錄不存在，INDEX 中 SaaS 區塊為「待新增」佔位）
- `subsidies/INDEX.md`：宣稱 55 件、連結 55 件、`programs/*.md` 55 件 ✅；`by-industry/*.md` 無死連結

### Orphaned Files

無。所有案例與方案檔皆被 INDEX 引用，INDEX 內無指向不存在檔案的連結。
