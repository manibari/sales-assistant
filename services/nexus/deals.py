"""Nexus deal service — CRUD for deals (the core entity)."""

import json

from database.connection import get_connection, row_to_dict, rows_to_dicts

VALID_STAGES = {"L0", "L1", "L2", "L3", "L4", "closed"}
MEDDIC_KEYS = {"metrics", "economic_buyer", "decision_criteria", "decision_process", "identify_pain", "champion"}


def create_deal(
    name: str,
    client_id: int,
    budget_range: str | None = None,
    timeline: str | None = None,
    budget_amount: float | None = None,
    budget_year: int | None = None,
) -> dict:
    meddic_init = json.dumps({k: None for k in MEDDIC_KEYS})
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO nx_deal (name, client_id, budget_range, timeline, meddic_json, budget_amount, budget_year)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)
                   RETURNING *""",
                (name, client_id, budget_range, timeline, meddic_init, budget_amount, budget_year),
            )
            return row_to_dict(cur)


def get_deal(deal_id: int) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT d.*, c.name AS client_name, c.industry AS client_industry
                   FROM nx_deal d
                   JOIN nx_client c ON d.client_id = c.id
                   WHERE d.id = %s""",
                (deal_id,),
            )
            return row_to_dict(cur)


def get_all_deals(status: str = "active") -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT d.*, c.name AS client_name, c.industry AS client_industry
                   FROM nx_deal d
                   JOIN nx_client c ON d.client_id = c.id
                   WHERE d.status = %s
                   ORDER BY d.last_activity_at ASC""",
                (status,),
            )
            return rows_to_dicts(cur)


def get_deals_by_urgency() -> list[dict]:
    """Get active deals sorted by idle days (most idle first)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT d.*, c.name AS client_name, c.industry AS client_industry,
                          EXTRACT(DAY FROM NOW() - d.last_activity_at)::INTEGER AS idle_days
                   FROM nx_deal d
                   JOIN nx_client c ON d.client_id = c.id
                   WHERE d.status = 'active'
                   ORDER BY idle_days DESC"""
            )
            return rows_to_dicts(cur)


def get_deals_needing_push(threshold_days: int = 14) -> list[dict]:
    """Get active deals idle for more than threshold_days."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT d.*, c.name AS client_name,
                          EXTRACT(DAY FROM NOW() - d.last_activity_at)::INTEGER AS idle_days
                   FROM nx_deal d
                   JOIN nx_client c ON d.client_id = c.id
                   WHERE d.status = 'active'
                     AND EXTRACT(DAY FROM NOW() - d.last_activity_at) > %s
                   ORDER BY idle_days DESC""",
                (threshold_days,),
            )
            return rows_to_dicts(cur)


def update_deal(deal_id: int, **fields) -> dict | None:
    if not fields:
        return get_deal(deal_id)
    allowed = {"name", "budget_range", "timeline", "meddic_json", "close_reason", "close_notes", "status", "stage", "budget_amount", "budget_year", "created_at"}
    filtered = {k: v for k, v in fields.items() if k in allowed}
    if not filtered:
        return get_deal(deal_id)
    set_clause = ", ".join(f"{k} = %s" for k in filtered)
    values = list(filtered.values()) + [deal_id]
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE nx_deal SET {set_clause}, updated_at = NOW() WHERE id = %s RETURNING *",
                values,
            )
            return row_to_dict(cur)


def advance_stage(deal_id: int, new_stage: str) -> dict | None:
    if new_stage not in VALID_STAGES:
        raise ValueError(f"Invalid stage: {new_stage}")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE nx_deal SET stage = %s, last_activity_at = NOW(),
                   updated_at = NOW() WHERE id = %s RETURNING *""",
                (new_stage, deal_id),
            )
            return row_to_dict(cur)


def close_deal(deal_id: int, reason: str, notes: str | None = None) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE nx_deal SET stage = 'closed', status = 'closed',
                   close_reason = %s, close_notes = %s,
                   updated_at = NOW() WHERE id = %s RETURNING *""",
                (reason, notes, deal_id),
            )
            return row_to_dict(cur)


def get_deals_by_client(client_id: int) -> list[dict]:
    """Get all deals for a specific client, with partners attached."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT d.*, c.name AS client_name, c.industry AS client_industry
                   FROM nx_deal d
                   JOIN nx_client c ON d.client_id = c.id
                   WHERE d.client_id = %s
                   ORDER BY d.last_activity_at DESC""",
                (client_id,),
            )
            deals = rows_to_dicts(cur)
            if not deals:
                return deals
            deal_ids = tuple(d["id"] for d in deals)
            cur.execute(
                """SELECT dp.deal_id, p.name AS partner_name, dp.role
                    FROM nx_deal_partner dp
                    JOIN nx_partner p ON dp.partner_id = p.id
                    WHERE dp.deal_id IN %s""",
                (deal_ids,),
            )
            partner_rows = rows_to_dicts(cur)
            partner_map: dict[int, list] = {}
            for row in partner_rows:
                partner_map.setdefault(row["deal_id"], []).append(row)
            for d in deals:
                d["partners"] = partner_map.get(d["id"], [])
            return deals


def get_deals_by_partner(partner_id: int) -> list[dict]:
    """Get all deals linked to a specific partner."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT d.*, c.name AS client_name, c.industry AS client_industry
                   FROM nx_deal d
                   JOIN nx_client c ON d.client_id = c.id
                   JOIN nx_deal_partner dp ON dp.deal_id = d.id
                   WHERE dp.partner_id = %s
                   ORDER BY d.last_activity_at DESC""",
                (partner_id,),
            )
            return rows_to_dicts(cur)


def touch_deal(deal_id: int) -> None:
    """Update last_activity_at to now."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE nx_deal SET last_activity_at = NOW() WHERE id = %s",
                (deal_id,),
            )


def get_meddic_progress(deal_id: int) -> dict:
    """Return MEDDIC completion status."""
    deal = get_deal(deal_id)
    if not deal or not deal.get("meddic_json"):
        return {"completed": 0, "total": 6, "missing": list(MEDDIC_KEYS)}
    meddic = deal["meddic_json"] if isinstance(deal["meddic_json"], dict) else json.loads(deal["meddic_json"])
    completed = [k for k in MEDDIC_KEYS if meddic.get(k)]
    missing = [k for k in MEDDIC_KEYS if not meddic.get(k)]
    return {"completed": len(completed), "total": 6, "missing": missing, "details": meddic}


# --- Deal-Partner M2M ---

def add_partner_to_deal(deal_id: int, partner_id: int, role: str | None = None) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO nx_deal_partner (deal_id, partner_id, role)
                   VALUES (%s, %s, %s)
                   RETURNING *""",
                (deal_id, partner_id, role),
            )
            return row_to_dict(cur)


def get_deal_partners(deal_id: int) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT dp.*, p.name AS partner_name, p.trust_level
                   FROM nx_deal_partner dp
                   JOIN nx_partner p ON dp.partner_id = p.id
                   WHERE dp.deal_id = %s""",
                (deal_id,),
            )
            return rows_to_dicts(cur)


def remove_partner_from_deal(deal_id: int, partner_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM nx_deal_partner WHERE deal_id = %s AND partner_id = %s",
                (deal_id, partner_id),
            )
            return cur.rowcount > 0


# --- Deal-Intel M2M ---

def link_intel_to_deal(deal_id: int, intel_id: int) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO nx_deal_intel (deal_id, intel_id)
                   VALUES (%s, %s)
                   RETURNING *""",
                (deal_id, intel_id),
            )
            result = row_to_dict(cur)
            # Touch deal in same connection to avoid lock
            cur.execute(
                "UPDATE nx_deal SET last_activity_at = NOW() WHERE id = %s",
                (deal_id,),
            )
            return result


def get_deal_intel(deal_id: int) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT di.*, i.title, i.raw_input, i.parsed_json, i.status, i.created_at AS intel_created_at
                   FROM nx_deal_intel di
                   JOIN nx_intel i ON di.intel_id = i.id
                   WHERE di.deal_id = %s
                   ORDER BY i.created_at DESC""",
                (deal_id,),
            )
            return rows_to_dicts(cur)


def unlink_intel_from_deal(deal_id: int, intel_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM nx_deal_intel WHERE deal_id = %s AND intel_id = %s",
                (deal_id, intel_id),
            )
            return cur.rowcount > 0
