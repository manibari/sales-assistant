"""Nexus tenders service — reads markdown case files as SSOT (no DB)."""

import logging
import time
from datetime import date, datetime
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

CASES_DIR = Path(__file__).resolve().parent.parent.parent / "materials" / "tenders" / "cases"

TRACKING_STATUSES = [
    "unreviewed",   # 未分類 — 剛爬進來
    "evaluating",   # 評估中
    "preparing",    # 準備中 — 決定投了，備標
    "submitted",    # 已投標
    "reviewing",    # 審查中
    "awarded",      # 得標
    "lost",         # 未得標
    "skipped",      # 不投
]

TRACKING_STATUS_LABELS = {
    "unreviewed": "未分類",
    "evaluating": "評估中",
    "preparing": "準備中",
    "submitted": "已投標",
    "reviewing": "審查中",
    "awarded": "得標",
    "lost": "未得標",
    "skipped": "不投",
}

TENDER_CLASS_MAP = {
    "採購預告": ["採購預告", "預告"],
    "公開徵求": ["公開徵求廠商提供參考資料"],
    "公開閱覽": ["公開閱覽"],
    "招標公告": [
        "公開招標", "選擇性招標", "招標公告",
        "公開取得報價單", "公開取得企劃書",
        "限制性招標", "經公開評選",
    ],
}


def _classify_tender_type(raw_type: str) -> str:
    """Classify a tender type string into one of 4 classes."""
    if not raw_type:
        return "招標公告"  # default
    for cls, keywords in TENDER_CLASS_MAP.items():
        if any(kw in raw_type for kw in keywords):
            return cls
    return "招標公告"

# Simple TTL cache
_cache: dict[str, tuple[float, object]] = {}
_TTL = 300  # 5 minutes


def _cached(key: str, fn):
    now = time.time()
    if key in _cache:
        ts, val = _cache[key]
        if now - ts < _TTL:
            return val
    val = fn()
    _cache[key] = (now, val)
    return val


def _parse_case(path: Path) -> dict | None:
    """Parse a single tender markdown file, return dict or None on error."""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return None

    if not text.startswith("---"):
        return None

    parts = text.split("---", 2)
    if len(parts) < 3:
        return None

    try:
        fm = yaml.safe_load(parts[1])
    except Exception:
        return None

    if not isinstance(fm, dict) or not fm.get("job_number"):
        return None

    # Calculate days_left from deadline
    days_left = None
    deadline_str = fm.get("deadline")
    if deadline_str:
        try:
            dl = datetime.strptime(str(deadline_str), "%Y-%m-%d").date()
            days_left = (dl - date.today()).days
        except (ValueError, TypeError):
            pass

    # Normalize budget display
    budget_raw = fm.get("budget")
    if budget_raw is not None:
        budget_amount = f"NT${int(budget_raw):,}" if isinstance(budget_raw, (int, float)) else str(budget_raw)
    else:
        budget_amount = None

    # Extract top-level category (e.g. "勞務" from "勞務類844-資料庫服務")
    raw_cat = fm.get("category", "")
    if raw_cat.startswith("勞務"):
        top_category = "勞務"
    elif raw_cat.startswith("財物"):
        top_category = "財物"
    elif raw_cat.startswith("工程"):
        top_category = "工程"
    else:
        top_category = "其他"

    # Classify tender into 4 classes
    raw_type = fm.get("type", "")
    tender_class = _classify_tender_type(raw_type)

    # Build human-readable URL (g0v frontend, not API JSON)
    unit_id = str(fm.get("unit_id", ""))
    job_num = str(fm.get("job_number", ""))
    if unit_id and job_num:
        reference_url = f"https://pcc.g0v.ronny.tw/tender/{unit_id}:{job_num}"
    else:
        reference_url = fm.get("source_url", "")

    # Extract markdown body (after second ---)
    body_md = parts[2].strip() if len(parts) > 2 else ""

    return {
        "job_number": str(fm["job_number"]),
        "name": fm.get("title", ""),
        "agency": fm.get("unit_name", ""),
        "category": top_category,
        "category_detail": raw_cat,
        "tender_type": fm.get("type", ""),
        "tender_class": tender_class,
        "deadline": str(deadline_str) if deadline_str else None,
        "budget_amount": budget_amount,
        "reference_url": reference_url,
        "days_left": days_left,
        "status": fm.get("status", "active"),
        "tracking_status": fm.get("tracking_status", "unreviewed"),
        "tags": fm.get("tags", []),
        "contact_name": fm.get("contact_name"),
        "contact_phone": fm.get("contact_phone"),
        "contact_email": fm.get("contact_email"),
        "file_path": str(path.relative_to(CASES_DIR.parent.parent.parent)),
        "has_notice": "## 投標須知" in body_md,
        "body_md": body_md,
    }


def _load_all_cases() -> list[dict]:
    """Load and parse all non-archived case files."""
    if not CASES_DIR.exists():
        return []
    results = []
    for p in sorted(CASES_DIR.glob("*.md")):
        rec = _parse_case(p)
        if rec:
            results.append(rec)
    return results


def get_all_tenders(
    status: str = "active",
    category: str | None = None,
    tracking_status: str | None = None,
) -> list[dict]:
    """Get all tenders, optionally filtered by status, category, tracking_status."""
    all_cases: list[dict] = _cached("all_cases", _load_all_cases)
    result = [t for t in all_cases if t["status"] == status]
    if category:
        result = [t for t in result if t["category"] == category]
    if tracking_status:
        result = [t for t in result if t["tracking_status"] == tracking_status]
    # Sort by deadline ASC (None last)
    result.sort(key=lambda t: t["deadline"] or "9999-99-99")
    return result


def get_tender(job_number: str) -> dict | None:
    """Get a single tender by job_number."""
    all_cases: list[dict] = _cached("all_cases", _load_all_cases)
    for t in all_cases:
        if t["job_number"] == job_number:
            return t
    return None


def get_tenders_expiring(within_days: int = 30) -> list[dict]:
    """Get tenders whose deadline is within N days (and not yet passed)."""
    all_cases: list[dict] = _cached("all_cases", _load_all_cases)
    result = [
        t for t in all_cases
        if t["status"] == "active"
        and t["days_left"] is not None
        and 0 <= t["days_left"] <= within_days
    ]
    result.sort(key=lambda t: t["days_left"])
    return result


def enrich_tender(job_number: str) -> dict:
    """Enrich a tender case with full pcc.gov.tw page content + notice document.

    Updates the markdown file in-place by appending content sections.
    Returns {"status": "enriched", "page_text_len": int, "notice_doc_len": int}.
    """
    from services.nexus.tender_detail_parser import enrich_tender_case

    # Find the case file
    md_file = _find_case_file(job_number)
    if not md_file:
        raise FileNotFoundError(f"Case file not found for {job_number}")

    # Read frontmatter
    text = md_file.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    fm = yaml.safe_load(parts[1])
    unit_id = str(fm.get("unit_id", ""))

    enriched = None

    if unit_id:
        # Try g0v API + pcc scrape (with fallback to search)
        enriched = enrich_tender_case(unit_id, job_number)

    if not enriched:
        # Fallback: search pcc.gov.tw directly by job_number
        from services.nexus.tender_detail_parser import search_pcc_by_job_number
        logger.info("Falling back to pcc search for %s", job_number)
        pcc_data = search_pcc_by_job_number(job_number)
        if pcc_data.get("page_text"):
            enriched = {
                "page_text": pcc_data["page_text"],
                "notice_doc": pcc_data.get("notice_doc", ""),
                "pcc_url": pcc_data.get("pcc_url", ""),
            }

    if not enriched:
        raise RuntimeError(f"Failed to enrich {job_number} — no data from g0v API or pcc search")

    page_text = enriched.get("page_text", "")
    notice_doc = enriched.get("notice_doc", "")
    pcc_url = enriched.get("pcc_url", "")

    # Backfill missing frontmatter fields from enriched data
    fm_updated = False
    backfill_map = {
        "budget": "budget",
        "deadline": "deadline",
        "contact_name": "contact_name",
        "contact_phone": "contact_phone",
        "contact_email": "contact_email",
        "type": "tender_type",
        "category": "category",
    }
    for fm_key, enriched_key in backfill_map.items():
        if not fm.get(fm_key) and enriched.get(enriched_key):
            val = enriched[enriched_key]
            # Parse budget string to int if possible
            if fm_key == "budget" and isinstance(val, str):
                import re
                nums = re.findall(r"[\d,]+", val)
                if nums:
                    try:
                        val = int(nums[0].replace(",", ""))
                    except ValueError:
                        continue
            fm[fm_key] = val
            fm_updated = True
            logger.info("Backfilled %s.%s = %s", job_number, fm_key, val)

    if fm_updated:
        parts[1] = "\n" + yaml.dump(fm, allow_unicode=True, default_flow_style=False)
        text = "---".join(parts)

    # Update the markdown file — append new sections if not already present
    new_sections = []

    if notice_doc and "## 投標須知" not in text:
        # Truncate to reasonable size for markdown
        doc_preview = notice_doc[:8000]
        new_sections.append(f"\n## 投標須知\n\n> 來源: [pcc.gov.tw]({pcc_url})\n\n{doc_preview}\n")

    if enriched.get("qualification") and "## 廠商資格" not in text:
        new_sections.append(f"\n## 廠商資格\n\n{enriched['qualification']}\n")

    if enriched.get("notes") and "## 附加說明" not in text:
        new_sections.append(f"\n## 附加說明\n\n{enriched['notes']}\n")

    if enriched.get("contract_period") and "## 履約期限" not in text:
        new_sections.append(f"\n## 履約期限\n\n{enriched['contract_period']}\n")

    if enriched.get("location") and "## 履約地點" not in text:
        new_sections.append(f"\n## 履約地點\n\n{enriched['location']}\n")

    if new_sections:
        text = text.rstrip() + "\n" + "\n".join(new_sections)

    if new_sections or fm_updated:
        md_file.write_text(text, encoding="utf-8")
        _cache.clear()
        logger.info("Enriched %s: %d sections added, fm_updated=%s", job_number, len(new_sections), fm_updated)

    return {
        "status": "enriched",
        "job_number": job_number,
        "sections_added": len(new_sections),
        "fields_backfilled": fm_updated,
        "page_text_len": len(page_text),
        "notice_doc_len": len(notice_doc),
    }


def enrich_all_active() -> list[dict]:
    """Enrich all active tenders that haven't been enriched yet."""
    results = []
    all_cases = _load_all_cases()
    for t in all_cases:
        if t["status"] != "active":
            continue

        md_file = _find_case_file(t["job_number"])
        if not md_file:
            continue

        content = md_file.read_text(encoding="utf-8")
        if "## 投標須知" in content:
            results.append({"job_number": t["job_number"], "status": "already_enriched"})
            continue

        try:
            result = enrich_tender(t["job_number"])
            results.append(result)
        except Exception as e:
            results.append({"job_number": t["job_number"], "status": "failed", "error": str(e)})
            logger.error("Failed to enrich %s: %s", t["job_number"], e)

    return results


def import_from_pcc_url(pcc_url: str) -> dict:
    """Import a tender directly from a pcc.gov.tw detail URL.

    Scrapes the page content and creates a case file.
    Works for tenders not found in g0v API.
    """
    import re
    from services.nexus.tender_detail_parser import fetch_pcc_page_content, _roc_to_iso

    pcc_data = fetch_pcc_page_content(pcc_url)
    page_text = pcc_data.get("page_text", "")
    if not page_text:
        raise RuntimeError("Failed to scrape pcc page — no content")

    # Parse structured fields from page text
    lines = page_text.split("\n")

    def _find_field(label: str) -> str:
        for i, line in enumerate(lines):
            if label in line:
                # Value is usually on the same line after tab, or next line
                parts = line.split("\t")
                if len(parts) >= 2:
                    return parts[-1].strip()
                elif i + 1 < len(lines):
                    return lines[i + 1].strip()
        return ""

    job_number = _find_field("標案案號")
    name = _find_field("標案名稱")
    agency = _find_field("機關名稱")
    tender_type = _find_field("招標方式")
    category = _find_field("標的分類")
    budget_raw = _find_field("預算金額")
    deadline_raw = _find_field("截止投標")
    opening_raw = _find_field("開標時間")
    contact_name = _find_field("聯絡人")
    contact_phone = _find_field("聯絡電話")
    contact_email = _find_field("電子郵件信箱")
    address = _find_field("機關地址")
    qualification = _find_field("廠商資格摘要")
    contract_period = _find_field("履約期限")
    location = _find_field("履約地點")
    notes = _find_field("附加說明")

    if not job_number:
        raise ValueError("Could not extract job_number from page")

    # Check if already exists
    existing = _find_case_file(job_number)
    if existing:
        return {"status": "already_exists", "job_number": job_number, "file": str(existing.name)}

    # Parse dates
    deadline_iso = _roc_to_iso(deadline_raw) if deadline_raw else None
    opening_iso = _roc_to_iso(opening_raw) if opening_raw else None

    # Parse budget
    budget_val = None
    budget_nums = re.findall(r"[\d,]+", budget_raw)
    if budget_nums:
        budget_val = int(budget_nums[0].replace(",", ""))

    # Auto-tag
    tags = []
    text = f"{name} {category}"
    tag_map = {
        "資安": ["資安"], "ISMS": ["ISMS", "資安"],
        "AI": ["AI"], "人工智慧": ["AI"], "影像辨識": ["影像辨識", "AI"],
        "大語言": ["LLM", "AI"], "系統維護": ["系統維護"],
        "軟體開發": ["軟體開發"], "資料庫": ["資料庫"], "雲端": ["雲端"],
    }
    for kw, t_list in tag_map.items():
        if kw in text:
            tags.extend(t_list)
    tags = list(dict.fromkeys(tags))[:8]

    # Build frontmatter
    from datetime import date as d_date
    fm = {
        "title": name,
        "unit_name": agency,
        "job_number": job_number,
        "unit_id": "",
        "type": tender_type,
        "category": category,
        "budget": budget_val,
        "deadline": deadline_iso,
        "opening_date": opening_iso,
        "contact_name": contact_name,
        "contact_phone": contact_phone,
        "contact_email": contact_email,
        "source_url": pcc_url,
        "scraped_date": d_date.today().isoformat(),
        "status": "active",
        "tags": tags,
    }

    budget_display = f"NT${budget_val:,}" if budget_val else budget_raw or "未公開"
    body = f"""# {name}

## 基本資訊

| 欄位 | 內容 |
|------|------|
| 招標機關 | {agency} |
| 標案案號 | {job_number} |
| 招標方式 | {tender_type} |
| 採購類別 | {category} |
| 預算金額 | {budget_display} |
| 截止日期 | {deadline_raw} |
| 開標日期 | {opening_raw} |

## 聯絡資訊

- **聯絡人**: {contact_name}
- **電話**: {contact_phone}
- **Email**: {contact_email}
- **地址**: {address}
"""

    if qualification:
        body += f"\n## 廠商資格\n\n{qualification}\n"
    if contract_period:
        body += f"\n## 履約期限\n\n{contract_period}\n"
    if location:
        body += f"\n## 履約地點\n\n{location}\n"
    if notes:
        body += f"\n## 附加說明\n\n{notes}\n"

    # Also append notice doc if downloaded
    notice_doc = pcc_data.get("notice_doc", "")
    if notice_doc:
        body += f"\n## 投標須知\n\n> 來源: [pcc.gov.tw]({pcc_url})\n\n{notice_doc[:8000]}\n"

    # Write file
    safe_name = re.sub(r"[^\w\u4e00-\u9fff]", "", name)[:20]
    filename = f"{job_number}-{safe_name}.md"
    filepath = CASES_DIR / filename

    content = f"---\n{yaml.dump(fm, allow_unicode=True, default_flow_style=False)}---\n\n{body}"
    filepath.write_text(content, encoding="utf-8")

    _cache.clear()
    logger.info("Imported from pcc URL: %s → %s", job_number, filepath.name)

    return {
        "status": "imported",
        "job_number": job_number,
        "name": name,
        "file": filepath.name,
        "has_notice": bool(notice_doc),
    }


def update_tracking_status(job_number: str, tracking_status: str) -> dict:
    """Update the tracking_status field in a tender's frontmatter."""
    if tracking_status not in TRACKING_STATUSES:
        raise ValueError(
            f"Invalid tracking_status '{tracking_status}'. "
            f"Valid: {', '.join(TRACKING_STATUSES)}"
        )

    md_file = _find_case_file(job_number)
    if not md_file:
        raise FileNotFoundError(f"Case file not found for {job_number}")

    text = md_file.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"Invalid frontmatter in {md_file.name}")

    fm = yaml.safe_load(parts[1])
    fm["tracking_status"] = tracking_status

    updated = f"---\n{yaml.dump(fm, allow_unicode=True, default_flow_style=False)}---{parts[2]}"
    md_file.write_text(updated, encoding="utf-8")

    _cache.clear()
    logger.info("Updated tracking_status for %s → %s", job_number, tracking_status)

    return {"job_number": job_number, "tracking_status": tracking_status}


def _find_case_file(job_number: str) -> Path | None:
    """Find a case file by job_number (partial filename match)."""
    if not CASES_DIR.exists():
        return None
    for p in CASES_DIR.glob("*.md"):
        if job_number in p.stem:
            return p
    return None
