"""Nexus deal service — CRUD for deals (the core entity)."""

import json

from database.connection import get_connection, row_to_dict, rows_to_dicts

VALID_STAGES = {"L0", "L1", "L2", "L3", "L4", "L5", "L6", "L7", "LOST", "HOLD"}
MEDDIC_KEYS = {
    "metrics",
    "economic_buyer",
    "decision_criteria",
    "decision_process",
    "identify_pain",
    "champion",
}


def create_deal(
    name: str,
    client_id: int,
    budget_range: str | None = None,
    timeline: str | None = None,
    budget_amount: float | None = None,
    budget_year: int | None = None,
    owner_id: int | None = None,
) -> dict:
    meddic_init = json.dumps({k: None for k in MEDDIC_KEYS})
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO nx_deal (name, client_id, budget_range, timeline, meddic_json, budget_amount, budget_year, owner_id)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING *""",
                (
                    name,
                    client_id,
                    budget_range,
                    timeline,
                    meddic_init,
                    budget_amount,
                    budget_year,
                    owner_id,
                ),
            )
            deal = row_to_dict(cur)
    # Auto-sync to memory md
    try:
        from services.nexus.memory import sync_from_deal
        sync_from_deal(deal["id"])
    except Exception:
        pass
    # Auto-sync to knowledge graph
    try:
        from services.nexus.graph import add_edge
        add_edge("client", client_id, "deal", deal["id"], "HAS_DEAL")
    except Exception:
        pass
    return deal


def get_deal(deal_id: int) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT d.*, c.name AS client_name, c.industry AS client_industry,
                          u.name AS owner_name
                   FROM nx_deal d
                   JOIN nx_client c ON d.client_id = c.id
                   LEFT JOIN nx_user u ON d.owner_id = u.id
                   WHERE d.id = %s""",
                (deal_id,),
            )
            return row_to_dict(cur)


def get_all_deals(status: str = "active", owner_id: int | None = None) -> list[dict]:
    where = "d.status = %s"
    params: list = [status]
    if owner_id is not None:
        where += " AND d.owner_id = %s"
        params.append(owner_id)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""SELECT d.*, c.name AS client_name, c.industry AS client_industry,
                           u.name AS owner_name
                    FROM nx_deal d
                    JOIN nx_client c ON d.client_id = c.id
                    LEFT JOIN nx_user u ON d.owner_id = u.id
                    WHERE {where}
                    ORDER BY d.last_activity_at ASC""",
                params,
            )
            return rows_to_dicts(cur)


def get_deals_by_urgency(owner_id: int | None = None) -> list[dict]:
    """Get active deals sorted by idle days (most idle first)."""
    where = "d.status = 'active'"
    params: list = []
    if owner_id is not None:
        where += " AND d.owner_id = %s"
        params.append(owner_id)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""SELECT d.*, c.name AS client_name, c.industry AS client_industry,
                           u.name AS owner_name,
                           EXTRACT(DAY FROM NOW() - d.last_activity_at)::INTEGER AS idle_days
                    FROM nx_deal d
                    JOIN nx_client c ON d.client_id = c.id
                    LEFT JOIN nx_user u ON d.owner_id = u.id
                    WHERE {where}
                    ORDER BY idle_days DESC""",
                params if params else None,
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
    allowed = {
        "name",
        "budget_range",
        "timeline",
        "meddic_json",
        "close_reason",
        "close_notes",
        "status",
        "stage",
        "budget_amount",
        "budget_year",
        "created_at",
        "owner_id",
    }
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
            result = row_to_dict(cur)
    # Auto-sync to memory md
    if result:
        try:
            from services.nexus.memory import sync_from_deal
            sync_from_deal(deal_id)
        except Exception:
            pass
    return result


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


def close_deal(
    deal_id: int,
    reason: str,
    outcome: str,  # 'won' | 'lost'
    notes: str | None = None,
    closed_by: int | None = None,
) -> dict | None:
    """Close a deal.

    Won deals keep stage=L7 and status='won'.
    Lost deals set stage='LOST' and status='lost'.
    """
    if outcome not in ("won", "lost"):
        raise ValueError(f"outcome must be 'won' or 'lost', got {outcome!r}")

    if outcome == "won":
        new_stage = "L7"
        new_status = "won"
    else:
        new_stage = "LOST"
        new_status = "lost"

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Snapshot old values for audit log
            cur.execute("SELECT stage, status, outcome FROM nx_deal WHERE id = %s", (deal_id,))
            old_row = cur.fetchone()
            if not old_row:
                return None
            old_values = {"stage": old_row[0], "status": old_row[1], "outcome": old_row[2]}

            cur.execute(
                """UPDATE nx_deal SET stage = %s, status = %s, outcome = %s,
                   close_reason = %s, close_notes = %s,
                   last_activity_at = NOW(), updated_at = NOW()
                   WHERE id = %s RETURNING *""",
                (new_stage, new_status, outcome, reason, notes, deal_id),
            )
            result = row_to_dict(cur)

            # Write audit log
            cur.execute(
                """INSERT INTO nx_audit_log
                   (table_name, record_id, action, changed_by, old_values, new_values)
                   VALUES ('nx_deal', %s, %s, %s, %s, %s)""",
                (
                    deal_id,
                    f"close_{outcome}",
                    closed_by,
                    json.dumps(old_values),
                    json.dumps({"stage": new_stage, "status": new_status, "outcome": outcome}),
                ),
            )

            return result


def hold_deal(deal_id: int, notes: str | None = None) -> dict | None:
    """Put a deal on hold."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE nx_deal SET stage = 'HOLD', status = 'hold',
                   close_notes = %s, updated_at = NOW()
                   WHERE id = %s RETURNING *""",
                (notes, deal_id),
            )
            return row_to_dict(cur)


def unhold_deal(deal_id: int, resume_stage: str = "L0") -> dict | None:
    """Resume a held deal back to active."""
    if resume_stage not in VALID_STAGES or resume_stage in ("LOST", "HOLD"):
        raise ValueError(f"Invalid resume stage: {resume_stage}")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE nx_deal SET stage = %s, status = 'active',
                   close_notes = NULL, last_activity_at = NOW(),
                   updated_at = NOW() WHERE id = %s RETURNING *""",
                (resume_stage, deal_id),
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
    meddic = (
        deal["meddic_json"]
        if isinstance(deal["meddic_json"], dict)
        else json.loads(deal["meddic_json"])
    )
    completed = [k for k in MEDDIC_KEYS if meddic.get(k)]
    missing = [k for k in MEDDIC_KEYS if not meddic.get(k)]
    return {
        "completed": len(completed),
        "total": 6,
        "missing": missing,
        "details": meddic,
    }


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
                   ON CONFLICT (deal_id, intel_id) DO NOTHING""",
                (deal_id, intel_id),
            )
            cur.execute(
                """SELECT * FROM nx_deal_intel
                   WHERE deal_id = %s AND intel_id = %s""",
                (deal_id, intel_id),
            )
            result = row_to_dict(cur)
            # Touch deal in same connection to avoid lock
            cur.execute(
                "UPDATE nx_deal SET last_activity_at = NOW() WHERE id = %s",
                (deal_id,),
            )
    # Auto-sync to knowledge graph
    try:
        from services.nexus.graph import add_edge
        add_edge("deal", deal_id, "intel", intel_id, "HAS_INTEL")
        add_edge("intel", intel_id, "deal", deal_id, "AFFECTS")
    except Exception:
        pass
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
