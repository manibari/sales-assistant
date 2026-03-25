"""Nexus tender DB service — CRUD for government tenders (nx_tender)."""

import json
import logging
from datetime import date, datetime
from pathlib import Path

import yaml

from database.connection import get_connection, row_to_dict, rows_to_dicts
from services.nexus.tenders import (
    CASES_DIR,
    TRACKING_STATUSES,
    _classify_tender_type,
    _find_case_file,
    _cache,
)

logger = logging.getLogger(__name__)

ALLOWED_FIELDS = {
    "title",
    "agency",
    "agency_id",
    "tender_type",
    "tender_class",
    "category",
    "category_detail",
    "budget",
    "deadline",
    "opening_date",
    "contact_name",
    "contact_phone",
    "contact_email",
    "source_url",
    "reference_url",
    "file_path",
    "tracking_status",
    "tags",
    "status",
    "scraped_date",
    "notes",
    "response_json",
    "client_id",
}


def create_tender(
    job_number: str,
    title: str,
    agency: str | None = None,
    agency_id: str | None = None,
    tender_type: str | None = None,
    tender_class: str | None = None,
    category: str | None = None,
    category_detail: str | None = None,
    budget: int | None = None,
    deadline: str | None = None,
    opening_date: str | None = None,
    contact_name: str | None = None,
    contact_phone: str | None = None,
    contact_email: str | None = None,
    source_url: str | None = None,
    reference_url: str | None = None,
    file_path: str | None = None,
    tracking_status: str = "unreviewed",
    tags: list[str] | None = None,
    scraped_date: str | None = None,
    client_id: int | None = None,
) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO nx_tender
                   (job_number, title, agency, agency_id, tender_type, tender_class,
                    category, category_detail, budget, deadline, opening_date,
                    contact_name, contact_phone, contact_email, source_url, reference_url,
                    file_path, tracking_status, tags, scraped_date, client_id)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING *""",
                (
                    job_number, title, agency, agency_id, tender_type, tender_class,
                    category, category_detail, budget, deadline, opening_date,
                    contact_name, contact_phone, contact_email, source_url, reference_url,
                    file_path, tracking_status, tags or [], scraped_date, client_id,
                ),
            )
            return row_to_dict(cur)


def get_tender(tender_id: int) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT t.*,
                          c.name AS client_name,
                          CASE WHEN t.deadline IS NOT NULL
                               THEN (t.deadline - CURRENT_DATE)
                          END AS days_left
                   FROM nx_tender t
                   LEFT JOIN nx_client c ON t.client_id = c.id
                   WHERE t.id = %s""",
                (tender_id,),
            )
            return row_to_dict(cur)


def get_tender_by_job_number(job_number: str) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT t.*,
                          c.name AS client_name,
                          CASE WHEN t.deadline IS NOT NULL
                               THEN (t.deadline - CURRENT_DATE)
                          END AS days_left
                   FROM nx_tender t
                   LEFT JOIN nx_client c ON t.client_id = c.id
                   WHERE t.job_number = %s""",
                (job_number,),
            )
            return row_to_dict(cur)


def get_all_tenders(
    status: str = "active",
    tracking_status: str | None = None,
    category: str | None = None,
) -> list[dict]:
    conditions = ["t.status = %s"]
    params: list = [status]

    if tracking_status:
        conditions.append("t.tracking_status = %s")
        params.append(tracking_status)
    if category:
        conditions.append("t.category = %s")
        params.append(category)

    where = " AND ".join(conditions)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""SELECT t.*,
                           c.name AS client_name,
                           CASE WHEN t.deadline IS NOT NULL
                                THEN (t.deadline - CURRENT_DATE)
                           END AS days_left
                    FROM nx_tender t
                    LEFT JOIN nx_client c ON t.client_id = c.id
                    WHERE {where}
                    ORDER BY CASE WHEN t.deadline IS NULL THEN 1 ELSE 0 END,
                             t.deadline ASC""",
                params,
            )
            return rows_to_dicts(cur)


def update_tender(tender_id: int, **fields) -> dict | None:
    if not fields:
        return get_tender(tender_id)
    filtered = {k: v for k, v in fields.items() if k in ALLOWED_FIELDS}
    if not filtered:
        return get_tender(tender_id)

    # Serialize tags and response_json
    if "tags" in filtered and isinstance(filtered["tags"], list):
        filtered["tags"] = filtered["tags"]  # psycopg2 handles list -> array
    if "response_json" in filtered and isinstance(filtered["response_json"], dict):
        filtered["response_json"] = json.dumps(filtered["response_json"], ensure_ascii=False)

    set_clause = ", ".join(f"{k} = %s" for k in filtered)
    values = list(filtered.values()) + [tender_id]
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE nx_tender SET {set_clause}, updated_at = NOW() WHERE id = %s RETURNING *",
                values,
            )
            return row_to_dict(cur)


def update_tracking_status(job_number: str, tracking_status: str) -> dict | None:
    """Dual-write: update tracking_status in both DB and markdown frontmatter."""
    if tracking_status not in TRACKING_STATUSES:
        raise ValueError(
            f"Invalid tracking_status '{tracking_status}'. "
            f"Valid: {', '.join(TRACKING_STATUSES)}"
        )

    # Update markdown first (raises FileNotFoundError if missing)
    from services.nexus.tenders import update_tracking_status as update_md_tracking
    update_md_tracking(job_number, tracking_status)

    # Update DB
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE nx_tender SET tracking_status = %s, updated_at = NOW()
                   WHERE job_number = %s RETURNING *""",
                (tracking_status, job_number),
            )
            row = row_to_dict(cur)
            if row:
                return row

    # If not in DB yet, return markdown result
    return {"job_number": job_number, "tracking_status": tracking_status}


def link_deal(tender_id: int, deal_id: int) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO nx_tender_deal (tender_id, deal_id)
                   VALUES (%s, %s)
                   ON CONFLICT (tender_id, deal_id) DO NOTHING
                   RETURNING *""",
                (tender_id, deal_id),
            )
            row = row_to_dict(cur)
            if row:
                return row
            # Already existed
            cur.execute(
                "SELECT * FROM nx_tender_deal WHERE tender_id = %s AND deal_id = %s",
                (tender_id, deal_id),
            )
            return row_to_dict(cur)


def unlink_deal(tender_id: int, deal_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM nx_tender_deal WHERE tender_id = %s AND deal_id = %s",
                (tender_id, deal_id),
            )
            return cur.rowcount > 0


def get_tender_deals(tender_id: int) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT td.*, d.name AS deal_name, d.stage AS deal_stage,
                          d.status AS deal_status, c.name AS client_name
                   FROM nx_tender_deal td
                   JOIN nx_deal d ON td.deal_id = d.id
                   JOIN nx_client c ON d.client_id = c.id
                   WHERE td.tender_id = %s
                   ORDER BY d.last_activity_at DESC""",
                (tender_id,),
            )
            return rows_to_dicts(cur)


# ---------------------------------------------------------------------------
# Markdown → DB sync
# ---------------------------------------------------------------------------


def sync_from_markdown(path: Path) -> dict | None:
    """Parse a single markdown tender file and UPSERT into nx_tender."""
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

    job_number = str(fm["job_number"])
    title = fm.get("title", "")
    agency = fm.get("unit_name", "")
    agency_id = str(fm.get("unit_id", "")) or None
    tender_type = fm.get("type", "")
    tender_class = _classify_tender_type(tender_type)

    # Category
    raw_cat = fm.get("category", "")
    if raw_cat.startswith("勞務"):
        category = "勞務"
    elif raw_cat.startswith("財物"):
        category = "財物"
    elif raw_cat.startswith("工程"):
        category = "工程"
    else:
        category = "其他"

    # Budget
    budget_raw = fm.get("budget")
    budget = None
    if isinstance(budget_raw, (int, float)):
        budget = int(budget_raw)

    # Dates
    deadline = str(fm["deadline"]) if fm.get("deadline") else None
    opening_date = str(fm["opening_date"]) if fm.get("opening_date") else None
    scraped_date = str(fm["scraped_date"]) if fm.get("scraped_date") else None

    # Reference URL
    unit_id = str(fm.get("unit_id", ""))
    if unit_id and job_number:
        reference_url = f"https://pcc.g0v.ronny.tw/tender/{unit_id}:{job_number}"
    else:
        reference_url = fm.get("source_url", "")

    file_path = str(path.relative_to(CASES_DIR.parent.parent.parent))

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO nx_tender
                   (job_number, title, agency, agency_id, tender_type, tender_class,
                    category, category_detail, budget, deadline, opening_date,
                    contact_name, contact_phone, contact_email, source_url, reference_url,
                    file_path, tracking_status, tags, scraped_date, status)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (job_number) DO UPDATE SET
                       title = EXCLUDED.title,
                       agency = EXCLUDED.agency,
                       agency_id = EXCLUDED.agency_id,
                       tender_type = EXCLUDED.tender_type,
                       tender_class = EXCLUDED.tender_class,
                       category = EXCLUDED.category,
                       category_detail = EXCLUDED.category_detail,
                       budget = EXCLUDED.budget,
                       deadline = EXCLUDED.deadline,
                       opening_date = EXCLUDED.opening_date,
                       contact_name = EXCLUDED.contact_name,
                       contact_phone = EXCLUDED.contact_phone,
                       contact_email = EXCLUDED.contact_email,
                       source_url = EXCLUDED.source_url,
                       reference_url = EXCLUDED.reference_url,
                       file_path = EXCLUDED.file_path,
                       tracking_status = EXCLUDED.tracking_status,
                       tags = EXCLUDED.tags,
                       scraped_date = EXCLUDED.scraped_date,
                       status = EXCLUDED.status,
                       updated_at = NOW()
                   RETURNING *""",
                (
                    job_number, title, agency, agency_id, tender_type, tender_class,
                    category, raw_cat, budget, deadline, opening_date,
                    fm.get("contact_name"), fm.get("contact_phone"), fm.get("contact_email"),
                    fm.get("source_url", ""), reference_url,
                    file_path, fm.get("tracking_status", "unreviewed"),
                    fm.get("tags", []), scraped_date,
                    fm.get("status", "active"),
                ),
            )
            return row_to_dict(cur)


def sync_all_markdown() -> dict:
    """Batch sync all markdown tender files to DB."""
    if not CASES_DIR.exists():
        return {"synced": 0, "errors": 0, "total": 0}

    synced = 0
    errors = 0
    total = 0

    for p in sorted(CASES_DIR.glob("*.md")):
        total += 1
        try:
            result = sync_from_markdown(p)
            if result:
                synced += 1
            else:
                errors += 1
        except Exception as e:
            errors += 1
            logger.error("Failed to sync %s: %s", p.name, e)

    return {"synced": synced, "errors": errors, "total": total}
