---
generated: 2026-08-09
total_subsidies: 65
total_archived_subsidies: 31
total_case_studies: 2
total_solutions: 3
---

# Materials Health Report

> Generated: 2026-08-09 (manual run via /material-health)

## Summary

| Check | Status | Issues |
|-------|--------|--------|
| Case study frontmatter | ✅ pass | 0 issues（內文仍有 2 處 TODO 佔位，非 frontmatter 問題） |
| Expired subsidies | ⚠️ warn | 1 件應歸檔 |
| Company info staleness | ⚠️ warn | 5 files stale（146 天），4 份仍是 TODO 佔位 |
| INDEX consistency | ⚠️ warn | subsidies INDEX 落後 10 件（07-27 產生後未再更新） |
| Orphaned files | ⚠️ warn | 10 個 program 檔未被任何 INDEX 引用 |
| Frontmatter 格式 | ⚠️ warn | 8 個 archived 檔 YAML 區塊未正確關閉（與上週相同，未修） |

本週主要惡化點：**subsidies INDEX 落差從 4 件擴大到 10 件**。INDEX.md 最後產生於 2026-07-27，之後 07-30 / 08-03 / 08-06 三次 scraper 執行共寫入新 program 檔但都沒重新產生 INDEX。建議跑一次 `/subsidy-scraper` 的 INDEX 重建，或在 scraper 尾端補上 INDEX regeneration 步驟（連續兩週同根因）。

## Details

### Case Studies (2 files)

必填欄位（client / industry / solution_type / year / outcome）兩份皆齊全，`scale` / `duration` / `tags` 也都有值。INDEX.md 與目錄檔案一致（2/2）。

| 檔案 | client | industry | solution_type | year | outcome |
|------|--------|----------|---------------|------|---------|
| `chimei-foods_2025.md` | 奇美食品 | 食品製造 | 數位轉型, 供應鏈管理 | 2025 | 品質異常反應時間縮短 60% |
| `example-tech_2025.md` | 範例科技 | 科技業 | AI 預測維護 | 2025 | 設備停機時間減少 40% |

⚠️ 內容品質備註（自 2026-07-12 起連續 5 週未動）：兩份案例的「客戶背景」章節都還是 `<!-- TODO: 填入客戶背景描述 -->`，規模／主要產品欄位空白。`example-tech_2025.md` 的「範例科技」是示範資料，建議確認要留還是刪。

### Subsidies (65 active / 31 archived)

**應歸檔（deadline 已過，今日 2026-08-09）— 1 件：**

| 檔案 | deadline | status |
|------|----------|--------|
| `programs/關鍵醫材國產量能自主整合補助計畫-115年度.md` | 2026-07-31 | active → 應移至 `archived/` |

**狀態不一致：** 無。65 件 active 檔的 `status` 欄位皆為 `active`。

**30 天內即將截止（提醒，非問題）：**

| 檔案 | deadline |
|------|----------|
| `國防需求產業化與創新鏈結推動計畫-115年度.md` | 2026-08-28 |
| `先進節能車輛國際拓展計畫-115年度.md` | 2026-08-31 |
| `創投加速創新創業計畫-115年度第2次公告.md` | 2026-08-31 |
| `製藥產業供應鏈韌性推動計畫-115年度.md` | 2026-08-31（**未在 INDEX 中**，見下） |

**Frontmatter 格式（archived/）— 8 件 YAML 未關閉（僅 1 個 `---` 分隔線），與 2026-08-02 報告相同，仍未修：**

- `半導體設備產業供應鏈驗證計畫-115年度.md`
- `在宅醫療科技實證推動計畫-115年度.md`
- `提升臺灣產業國際形象計畫Taiwan-Excellence為品牌推廣海外市場.md`
- `民生消費品產業數位加值轉型計畫.md`
- `民生產業轉型加值計畫.md`
- `臺中市地方產業創新研發推動計畫-地方型SBIR-115年度.md`
- `臺日關鍵優勢產業合作補助計畫-115年度.md`
- `製造業最低工資補貼.md`

### Company Info (5 files) — 全數 stale

5 檔最後修改都是 **2026-03-16**（距今 146 天，門檻 90 天）：

| 檔案 | 最後修改 | TODO 佔位 |
|------|----------|-----------|
| `profile.md` | 2026-03-16 | ⚠️ 有 |
| `capabilities.md` | 2026-03-16 | 無 |
| `methodology.md` | 2026-03-16 | ⚠️ 有 |
| `differentiators.md` | 2026-03-16 | ⚠️ 有 |
| `team.md` | 2026-03-16 | ⚠️ 有 |

### INDEX Mismatches

**subsidies/INDEX.md**（產生於 2026-07-27，宣稱 55 件；實際 programs/ 有 65 件）— 以下 10 檔存在但未被索引（同時也是本週的 orphaned files）：

1. `中小企業因應淨零碳趨勢提升綠色競爭力.md`
2. `中小企業減碳服務站.md`
3. `公用設備與系統效率提升示範計畫.md`
4. `商業服務業深根市場創價成長計畫.md`
5. `推動節能績效保證ESPC補助計畫.md`
6. `數位商圈應用能力提升計畫.md`
7. `數據驅動中小企業品牌躍升計畫.md`
8. `數據驅動製造業研發創新輔導.md`
9. `服務業AI人才培育.md`（deadline 2026-12-20）
10. `製藥產業供應鏈韌性推動計畫-115年度.md`（deadline 2026-08-31，**即將截止卻不在 INDEX**，最優先補）

另外 INDEX 頂部的「⚠️ 優先處理 6 件」清單仍含已過期的 `關鍵醫材國產量能自主整合補助計畫`，重建 INDEX 時會一併修正。

INDEX 中引用的 55 個檔案全部存在（無 broken link）。

**case-studies/INDEX.md** ✅ 一致（2/2）。
**solutions/INDEX.md** ✅ 一致（3/3，`ai-data/` 2 件 + `consulting/` 1 件；`saas/` 目錄尚未建立，INDEX 中標記「待新增」屬已知狀態）。

## Recommended Actions

1. **（優先）重建 subsidies/INDEX.md** — 落差已連續兩週擴大（4 → 10 件），且含一件 08-31 截止的計畫。建議在 subsidy-scraper 流程尾端加上 INDEX regeneration，杜絕根因。
2. 將 `關鍵醫材國產量能自主整合補助計畫-115年度.md` 移入 `programs/archived/` 並更新 status。
3. 修復 8 個 archived 檔的 YAML frontmatter（補上關閉的 `---`）。
4. 更新 `company/` 五檔（146 天未動），至少補齊 profile / methodology / differentiators / team 的 TODO 佔位。
5. 決定 `example-tech_2025.md` 示範案例去留；補齊兩份案例的客戶背景章節。
