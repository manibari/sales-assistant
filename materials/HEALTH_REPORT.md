# Materials Health Report

> Generated: 2026-03-25

## Summary

| Check | Status | Issues |
|-------|--------|--------|
| Case study frontmatter | PASS | 0 issues |
| Case study content | WARN | 2 files have TODO placeholders |
| Expired subsidies | WARN | 1 to archive |
| Subsidy missing status | WARN | 6 files missing `status` field |
| Company info staleness | PASS | 0 stale files (all updated 2026-03-16) |
| Company TODO placeholders | WARN | 4 files with unfilled content |
| INDEX consistency | PASS | 0 mismatches |
| Orphaned files | PASS | 0 orphans |
| Solutions coverage | WARN | `saas/` category empty |

## Details

### Case Studies

Frontmatter 完整性 — 全部通過（client, industry, solution_type, year, outcome 皆有值）。

內容 TODO — 以下檔案有尚未填寫的區塊：

| 檔案 | 問題 |
|------|------|
| `chimei-foods_2025.md` | `<!-- TODO: 填入客戶背景描述 -->`，規模/主要產品/挑戰皆為空 |
| `example-tech_2025.md` | `<!-- TODO: 填入客戶背景描述 -->`，規模/主要產品/挑戰皆為空 |

### Subsidies

#### 應歸檔（deadline 已過）

| 補助名稱 | 截止日期 | 建議動作 |
|----------|----------|----------|
| 服務業創新研發計畫 (SIIR) — 115年度 | 2026-01-30 | 移至 `archived/`，第二梯次待公告後建新檔 |

#### 缺少 `status` 欄位

以下 6 個 program 檔案 frontmatter 未設定 `status` 欄位：

1. `SBIR-企業跨域研發補助.md`
2. `中小型製造業低碳及智慧化升級轉型個案補助.md`
3. `協助傳統產業技術開發計畫-CITD-115年度第1梯次.md`
4. `小型企業創新研發計畫-SBIR-115年度.md`
5. `服務業創新研發計畫-SIIR-115年度.md`
6. `補助中小用戶導入節能服務.md`

#### 即將到期（30 天內）

| 補助名稱 | 截止日期 |
|----------|----------|
| 商業服務業節能設備補助 | 2026-04-10 |
| 中小型製造業接班傳承AI應用數位轉型 | 2026-04-27 |

#### INDEX 一致性

- INDEX 宣稱 50 筆，programs/ 實際 50 筆 — 一致
- 無 `archived/` 目錄（已過期檔案尚未歸檔）

### Company Info

所有 5 檔皆於 2026-03-16 更新，未超過 90 天門檻。

TODO / 待填內容：

| 檔案 | 問題 |
|------|------|
| `profile.md` | `<!-- TODO: 請填入實際公司資訊 -->`，公司介紹/產業列表為空 |
| `team.md` | `<!-- TODO: 請填入實際團隊資訊 -->`，團隊/夥伴描述為空 |
| `methodology.md` | `<!-- TODO: 請填入實際方法論 -->`，AI/管顧/品控方法論為空 |
| `differentiators.md` | `<!-- TODO: 請填入實際差異化優勢 -->`，ICP 描述為空 |

### Solutions

- `ai-data/`: 2 個方案（predictive-maintenance, data-driven-platform）— INDEX 一致
- `consulting/`: 1 個方案（digital-transformation）— INDEX 一致
- `saas/`: 0 個方案 — INDEX 標記「待新增」

### Orphaned Files

無孤立檔案。所有 .md 檔皆已在對應 INDEX 中登錄。
