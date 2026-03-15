# Sales Enablement Material Library

統一管理公司銷售素材的中央資料庫，支援自動化更新與對話驅動簡報組裝。

## 目錄結構

| 目錄 | 用途 | 維護方式 |
|------|------|----------|
| `company/` | 公司簡介、能力、團隊、方法論 | 手動維護 |
| `case-studies/` | 客戶案例庫（含 frontmatter tags） | 手動維護 |
| `solutions/` | 方案模板（AI/Data、管顧、SaaS） | 手動維護 |
| `subsidies/` | 政府補助資訊 | 自動產生（subsidy-scraper） |
| `clients/` | CRM 客戶索引 | 自動產生（crm-projection） |
| `templates/` | 簡報模板 .pptx | 手動維護 |
| `presentations/` | 已產出的簡報（output） | 自動產生（sales-material skill） |

## 案例 Frontmatter 格式

```yaml
---
client: 公司名稱
industry: 產業
solution_type: [方案類型]
scale: small | medium | large
duration: 專案期間
year: 年份
outcome: "量化成果"
tags: [技術標籤]
---
```

## 方案模板格式

```yaml
---
name: 方案名稱
category: ai-data | consulting | saas
target_industry: [適用產業]
typical_duration: 期間
typical_budget: 預算範圍
tags: [技術標籤]
---
```

## 自動更新機制

- **subsidy-scraper**: 每週一/四 08:00 爬取政府補助公告 → 更新 `subsidies/`
- **crm-projection**: 每日 07:00 同步 nx_client → 更新 `clients/INDEX.md`
- **material-health**: 每週日 09:00 檢查素材完整性

## 使用方式

1. **手動查找**: 直接瀏覽各目錄的 INDEX.md
2. **對話組裝**: 告訴 Claude「幫我做 X 公司的簡報」，自動配對素材並產出 PPTX
3. **補助匹配**: 告訴 Claude「X 產業有什麼補助」，自動查詢 subsidies/by-industry/
