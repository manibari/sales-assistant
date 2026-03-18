# Taiwan Government Tender Scraper Pattern

Recorded: 2026-03-18
Source: Sprint implementing 政府標案 feature for Project Nexus

## Architecture

- **Data source 1**: g0v API `https://pcc-api.openfun.app/api/tender/listbydate?date=YYYY-MM-DD`
  - Returns all announcement types including 決標公告 — must filter these out
  - Field structure: `job_number` is top-level (NOT inside `brief{}`)
  - Some tenders exist on pcc.gov.tw but NOT in g0v API

- **Data source 2**: Manual import via pcc.gov.tw URL (Playwright scrape)
  - For tenders not in g0v API
  - Extracts structured fields from page text using tab-separated field parsing

- **Storage**: Markdown-file SSOT (`materials/tenders/cases/`)
  - See `markdown-file-ssot` skill for pattern

## Tender Classification (4 types)

```python
TENDER_CLASS_MAP = {
    "採購預告": ["採購預告", "預告"],
    "公開徵求": ["公開徵求廠商提供參考資料"],  # NOTE: exact match only
    "公開閱覽": ["公開閱覽"],
    "招標公告": [
        "公開招標", "選擇性招標", "招標公告",
        "公開取得報價單", "公開取得企劃書",  # ← these are 招標公告, NOT 公開徵求
        "限制性招標", "經公開評選",
    ],
}
```

**Common bug**: "公開取得報價單或企劃書" was wrongly classified as "公開徵求" — fix: use keyword-in-string match, and ensure "公開徵求廠商提供參考資料" is the only match for 公開徵求.

## Keyword Filtering for Enrichment

Only enrich (fetch full content) for tenders matching these keywords:
```python
ENRICH_KEYWORDS = [
    "AI", "人工智慧", "大語言", "LLM", "機器學習",
    "影像辨識", "智慧", "資訊系統", "資訊服務",
    "軟體", "系統建置", "系統維護", "網站", "平台",
    "雲端", "資安", "ISMS", "資料庫", "監控系統",
    "委外服務", "磁碟陣列", "伺服器",
]
```

## ODT Parsing Fix

Using `python-docx2txt` / raw XML parsing — must iterate at **paragraph level** (`text:p`) not text node level, or each XML text node appears on its own line:

```python
from lxml import etree
NS = {"text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0"}

def _parse_odt(content: bytes) -> str:
    import zipfile, io
    with zipfile.ZipFile(io.BytesIO(content)) as z:
        xml = z.read("content.xml")
    root = etree.fromstring(xml)
    paragraphs = []
    for p in root.iter("{urn:oasis:names:tc:opendocument:xmlns:text:1.0}p"):
        text = "".join(p.itertext()).strip()
        if text:
            paragraphs.append(text)
    return "\n".join(paragraphs)
```

## Deadline Issue

Many tenders from g0v API have no deadline because:
- 決標公告 (awarded contracts) have no deadline — skip by checking type contains "決標" or "無法決標"
- 採購預告 legitimately may have no deadline date

## Script Location

`scripts/tender_scraper.py` — standalone Python scraper
`scripts/tender-scraper.sh` — shell wrapper
`services/nexus/tenders.py` — service layer
`services/nexus/tender_detail_parser.py` — Playwright + document parsing
`backend/routers/nexus/tenders.py` — FastAPI router
`frontend/src/app/tenders/` — frontend pages
