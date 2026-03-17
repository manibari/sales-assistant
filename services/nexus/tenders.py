"""Nexus tenders service — reads markdown case files as SSOT (no DB)."""

import time
from datetime import date, datetime
from pathlib import Path

import yaml

CASES_DIR = Path(__file__).resolve().parent.parent.parent / "materials" / "tenders" / "cases"

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

    # Build human-readable URL (g0v frontend, not API JSON)
    unit_id = str(fm.get("unit_id", ""))
    job_num = str(fm.get("job_number", ""))
    if unit_id and job_num:
        reference_url = f"https://pcc.g0v.ronny.tw/tender/{unit_id}:{job_num}"
    else:
        reference_url = fm.get("source_url", "")

    return {
        "job_number": str(fm["job_number"]),
        "name": fm.get("title", ""),
        "agency": fm.get("unit_name", ""),
        "category": top_category,
        "category_detail": raw_cat,
        "tender_type": fm.get("type", ""),
        "deadline": str(deadline_str) if deadline_str else None,
        "budget_amount": budget_amount,
        "reference_url": reference_url,
        "days_left": days_left,
        "status": fm.get("status", "active"),
        "tags": fm.get("tags", []),
        "contact_name": fm.get("contact_name"),
        "contact_phone": fm.get("contact_phone"),
        "contact_email": fm.get("contact_email"),
        "file_path": str(path.relative_to(CASES_DIR.parent.parent.parent)),
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


def get_all_tenders(status: str = "active", category: str | None = None) -> list[dict]:
    """Get all tenders, optionally filtered by status and category."""
    all_cases: list[dict] = _cached("all_cases", _load_all_cases)
    result = [t for t in all_cases if t["status"] == status]
    if category:
        result = [t for t in result if t["category"] == category]
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
