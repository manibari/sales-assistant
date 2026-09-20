---
generated: 2026-09-20
total_subsidies: 61
total_archived_subsidies: 37
total_case_studies: 2
total_solutions: 3
---

# Materials Health Report

> Generated: 2026-09-20 (manual run via /sales-material-health)

## Summary

| Check | Status | Issues |
|-------|--------|--------|
| Case study frontmatter | ✅ pass | 0 issues（必填欄位齊全；內文 TODO 佔位另計） |
| Expired subsidies | ✅ pass | 0 件應歸檔（最近截止 09-24，**剩 4 天**） |
| Company info staleness | ⚠️ warn | 5 files stale（188 天），4 份仍是 TODO 佔位 |
| INDEX consistency | ✅ pass | 0 mismatches（61/61、2/2、3/3） |
| Orphaned files | ✅ pass | 0 orphans |
| Frontmatter 格式 | ⚠️ warn | 8 個 archived 檔 YAML 未關閉（**連續 7 週未修，本週已定位根因**） |

本週無新增過期補助、INDEX 落差或孤兒檔。兩項 warn 都是既有問題，其中 YAML 格式問題本週查出根因，可一次修掉。

---

## 本週該動手的兩件事

1. **09-24 截止的補助只剩 4 天** — 自適應衛星通訊酬載與多軌衛星地面終端開發補助計畫（115年度）。要投就這週決定。
2. **修掉 8 個 archived 檔的 YAML**（根因已定位，見下方「Frontmatter 格式」）— 連續 7 週掛著，一次 sed 可解。

---

## Details

### Case Studies

必填欄位（client / industry / solution_type / year / outcome）**兩個檔案全部齊全**：

| 檔案 | client | industry | solution_type | year | outcome |
|------|--------|----------|---------------|------|---------|
| chimei-foods_2025.md | 奇美食品 | 食品製造 | 數位轉型, 供應鏈管理 | 2025 | 品質異常反應時間縮短 60% |
| example-tech_2025.md | 範例科技 | 科技業 | AI 預測維護 | 2025 | 設備停機時間減少 40% |

⚠️ **內容層面的問題（不算 frontmatter 失敗，但影響可用性）**：

- `example-tech_2025.md` 的 client 是「**範例科技**」— 這是建庫時的示範資料，不是真實案例。它同時被列進 `case-studies/INDEX.md`（2 處）和 `solutions/ai-data/predictive-maintenance.md:51` 的案例引用。**目前「2 則案例」實際只有 1 則是真的。**
- 兩個檔案的「客戶背景描述」段落都還是 `<!-- TODO: 填入客戶背景描述 -->`（`example-tech_2025.md:16`、`chimei-foods_2025.md:16`）。做提案抓素材時這段會是空的。

### Subsidies

**0 件應歸檔。** 61 件 active 的截止日全部 ≥ 今日（2026-09-20）。

近期截止（INDEX 已標 ⚠️，共 7 件，與實際相符）：

| 截止日 | 剩餘 | 計畫 |
|--------|------|------|
| 2026-09-24 | **4 天** | 自適應衛星通訊酬載與多軌衛星地面終端開發補助計畫（115年度） |
| 2026-09-29 | 9 天 | 雲市集工業館 — 雲端解決方案點數補助計畫（115年度） |
| 2026-09-30 | 10 天 | 亞灣智慧網通國際拓點與服務應用示範研發計畫（115年度） |
| 2026-09-30 | 10 天 | 提升商業服務業營運效能強化韌性計畫 — 整合型補助 |
| 2026-10-30 | 40 天 | 臺法創新研發合作補助計畫（115年度） |
| 2026-10-30 | 40 天 | 關鍵礦物應用高值化推動計畫（115年度） |
| 2026-10-30 | 40 天 | 雲市集工業館 — AI工具庫點數補助計畫（115年度） |

**狀態一致性**：61 件全為 `status: active`，無「status 非 active 卻留在 programs/」的情形。

**關於 41 件 `deadline: ""`** — 這**不是缺漏**。這些是長期／隨到隨審或梯次待公告的計畫，一律有 `deadline_text` 說明（例如 SBIR 跨域：「115年度第一梯次已結束，下一梯次待公告」）。已逐檔確認：**空 deadline 且無 deadline_text 的檔案為 0**。

### Company Info

**5 個檔案全部超過 90 天門檻**（mtime 均為 2026-03-16，**188 天**未更新）：

| 檔案 | 未更新天數 | TODO 佔位 |
|------|-----------|-----------|
| profile.md | 188 | ⚠️ `<!-- TODO: 請填入實際公司資訊 -->` |
| differentiators.md | 188 | ⚠️ `<!-- TODO: 請填入實際差異化優勢 -->` |
| team.md | 188 | ⚠️ `<!-- TODO: 請填入實際團隊資訊 -->` |
| methodology.md | 188 | ⚠️ `<!-- TODO: 請填入實際方法論 -->` |
| capabilities.md | 188 | — |

**這是整份報告裡最實質的缺口**：公司基本資料 5 份有 4 份從建庫（2026-03-16）至今沒填過，還是骨架。任何 `sales-material` 組裝出來的提案，「我們是誰 / 為什麼選我們 / 團隊 / 方法論」四段都拿不到內容。

補充：使用者同時代表 **正傑科技** 與 **詠鋐智能** 兩家公司，填寫前需先決定 `company/` 是單一公司還是要分 org（參考 memory `user_companies.md` / `project_org_switching.md` — org switching 目前 deferred）。

### INDEX Mismatches

**全部一致，0 mismatch。**

| INDEX | 宣告 | 磁碟實際 | 結果 |
|-------|------|---------|------|
| subsidies/INDEX.md | 61 件 active | 61 個 `programs/*.md` | ✅ 雙向比對 0 落差（無孤兒、無死連結） |
| case-studies/INDEX.md | 2 則 | 2 個 `.md` | ✅ |
| solutions/INDEX.md | 3 個方案 | 3 個 `.md`（ai-data×2, consulting×1） | ✅ |
| subsidies/by-industry/ | 8 個分類檔 | — | ✅ 內部 `../programs/*.md` 連結全部有效 |

小提醒（非錯誤）：`solutions/INDEX.md` 列有 `saas/` 分類但磁碟上無此目錄，表格內容是 `<!-- 待新增 -->` 佔位，屬已知待辦。

### Orphaned Files

**0 orphans。** case-studies、solutions、subsidies/programs 的每個 `.md` 都被對應 INDEX 引用。

### Frontmatter 格式（本週定位到根因）

`programs/archived/` 下 **8 個檔案的 YAML frontmatter 從未關閉**，已連續 7 週出現在報告中。

**根因**：歸檔時把 `status: active` 改成 `expired`，**吃掉了 status 行後面的換行**，導致結尾 `---` 黏在同一行：

```
status: expired---        ← 應為 "status: expired" + 換行 + "---"
```

後果：該檔只剩 1 個 `---` 分隔符，YAML 區塊不封閉。任何解析 frontmatter 的程式會讀到整份檔案內容，或把 status 解析成字串 `"expired---"`。

受影響檔案（全部為同一模式）：

| 檔案 | 行號 |
|------|------|
| 半導體設備產業供應鏈驗證計畫-115年度.md | 16 |
| 民生產業轉型加值計畫.md | 16 |
| 臺中市地方產業創新研發推動計畫-地方型SBIR-115年度.md | 16 |
| 在宅醫療科技實證推動計畫-115年度.md | 16 |
| 臺日關鍵優勢產業合作補助計畫-115年度.md | 16 |
| 提升臺灣產業國際形象計畫Taiwan-Excellence為品牌推廣海外市場.md | 17 |
| 民生消費品產業數位加值轉型計畫.md | 18 |
| 製造業最低工資補貼.md | 19 |

**修法**（未執行，本 skill 為 report-only）：

```bash
cd materials/subsidies/programs/archived
grep -l 'expired---' *.md | while read f; do
  perl -0pi -e 's/status: expired---/status: expired\n---/' "$f"
done
```

**防再發**：歸檔步驟是 `~/.claude/skills/gov-subsidy-scraper/scraper.md:119` 的自然語言指示（"Change frontmatter status: active → expired"），沒有程式碼把關。建議把該行改成明確要求「只替換 `active` 這個字，不要動行尾換行」，或在 scraper 收尾加一道 `grep -c '^---$' == 2` 的檢查。

### 資料品質觀察（非 skill 定義的檢查項）

`subsidies/INDEX.md` 有數列的「主辦機關」欄塞進了整段爬下來的聯絡資訊，含 email 與電話，例如：

- 補助中小用戶導入節能服務 → 「主辦單位 經濟部能源署 執行單位 台灣綠色生產力基金會…黃瀚民工程師／02-29106067#631…」
- 提供30人以下的中小微企業優惠貸款
- 提供為員工加薪的中小企業融資信用保證
- 提供投資智慧機械與資安5G系統…
- 協助食品業以TAIWAN SELECT共同品牌進軍海外市場

來源是 `programs/*.md` 的 `agency` 欄位被爬蟲灌入整塊 contact blob。不影響比對與連結，但 INDEX 表格會被撐爆、且這些檔案若進到客戶簡報會很難看。建議在 scraper 的 `agency` 欄加長度上限或只取第一個機關名。
