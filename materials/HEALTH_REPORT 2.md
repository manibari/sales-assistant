# Materials Health Report

> Generated: 2026-03-18
> Scope: `materials/` — frontmatter, expiry, placeholders, INDEX consistency

## Summary

| Category | Status | Issues |
|----------|--------|--------|
| Case Studies | ⚠ Warning | 2 files are unfilled templates |
| Solutions | ✅ OK | All frontmatter complete, content substantive |
| Company | ❌ Critical | All 5 files are placeholders |
| Subsidies | ⚠ Warning | 1 expired-but-active, 5 empty fields, 32 no deadline |
| Tenders INDEX | ⚠ Warning | 94 files on disk not in INDEX |
| Other INDEXes | ✅ OK | case-studies, solutions, subsidies all consistent |

**Total issues: 7 critical + warnings**

---

## 1. Expired Subsidies (deadline < 2026-03-18, status still `active`)

| File | Deadline | Note |
|------|----------|------|
| `subsidies/programs/服務業創新研發計畫-SIIR-115年度.md` | 2026-01-30 | 第一梯次已截止；第二梯次預計115年7月收件 |

**Action**: Update deadline to 第二梯次日期 or set `status: closed`.

## 2. Subsidies with Empty Required Fields

| File | Empty Fields |
|------|-------------|
| `subsidies/programs/創新育成補助.md` | `funding_amount`, `eligibility` |
| `subsidies/programs/商業服務業節能設備補助.md` | `funding_amount` |
| `subsidies/programs/提供為員工加薪的中小企業融資信用保證.md` | `funding_amount` |
| `subsidies/programs/提供碳健檢與AI財務服務.md` | `funding_amount` |
| `subsidies/programs/產業升級創新平台輔導計畫-主題式研發計畫.md` | `eligibility` |

## 3. Subsidies with No Deadline (32 files)

These programs have `deadline: ""` — most are rolling/on-demand (常態受理). Not necessarily an error, but should be verified periodically. The programs use `deadline_text` for human-readable schedule info.

**Status breakdown**: All 50 active programs have `status: active`. No `closed` or `pending` entries exist.

## 4. Company Files — All Placeholders

All 5 files in `company/` contain `<!-- TODO -->` markers and empty table cells:

| File | Content |
|------|---------|
| `company/profile.md` | Empty — no company info filled in |
| `company/capabilities.md` | Empty — service descriptions missing |
| `company/team.md` | Empty — team member details missing |
| `company/methodology.md` | Empty — methodology not documented |
| `company/differentiators.md` | Empty — competitor analysis not filled in |

**Action**: Fill in actual company information for both 正傑科技 and 詠鋐智能.

## 5. Case Studies — Template Bodies

Frontmatter is complete for both files, but body content is unfilled:

| File | Frontmatter | Body |
|------|-------------|------|
| `case-studies/chimei-foods_2025.md` | ✅ Complete | ❌ Template (TODO markers, empty cells) |
| `case-studies/example-tech_2025.md` | ✅ Complete | ❌ Template (TODO markers, empty cells) |

## 6. Solutions — OK

All 3 solution files have complete frontmatter and substantive content:
- `ai-data/predictive-maintenance.md` ✅
- `ai-data/data-driven-platform.md` ✅
- `consulting/digital-transformation.md` ✅

**Note**: `solutions/saas/` directory is empty — no SaaS solution templates yet.

## 7. INDEX Consistency

| INDEX File | Indexed | On Disk | Orphan Refs | Unlisted |
|------------|---------|---------|-------------|----------|
| `case-studies/INDEX.md` | 2 | 2 | 0 | 0 |
| `solutions/INDEX.md` | 3 | 3 | 0 | 0 |
| `subsidies/INDEX.md` | 30 unique | 30 | 0 | 0 |
| `tenders/INDEX.md` | 39 | 133 | 0 | **94** |

**Tenders**: 94 case files exist on disk but are not in INDEX. INDEX only lists cases within the bidding window (by design — `tender-scraper` auto-generates INDEX for active cases). The unlisted files are either newly scraped or past-deadline cases awaiting archival.

## Recommended Actions

1. **[High]** Fill `company/` files with actual company information
2. **[High]** Complete case study body content (remove TODO markers)
3. **[Medium]** Update SIIR subsidy deadline or mark as closed
4. **[Medium]** Fill empty `funding_amount`/`eligibility` fields in 5 subsidy files
5. **[Low]** Archive expired tender cases not in INDEX (94 files)
6. **[Low]** Add SaaS solution templates to `solutions/saas/`
