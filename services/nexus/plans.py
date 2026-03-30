"""Nexus plan service — CRUD for strategy plans (annual, product, internal, proposal)."""

from database.connection import get_connection, row_to_dict, rows_to_dicts

VALID_PLAN_TYPES = {"annual", "product", "internal", "proposal"}
VALID_STATUSES = {"draft", "active", "archived"}


def create_plan(
    title: str,
    plan_type: str = "annual",
    fiscal_year: int | None = None,
    body: str | None = None,
    deal_id: int | None = None,
    client_id: int | None = None,
    notes: str | None = None,
) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO nx_plan (title, plan_type, fiscal_year, body, deal_id, client_id, notes)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)
                   RETURNING *""",
                (title, plan_type, fiscal_year, body, deal_id, client_id, notes),
            )
            plan = row_to_dict(cur)
    # Auto-sync to knowledge graph
    if client_id and plan:
        try:
            from services.nexus.graph import add_edge
            add_edge("client", client_id, "plan", plan["id"], "HAS_PLAN")
        except Exception:
            pass
    return plan


def get_plan(plan_id: int) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT p.*,
                          c.name AS client_name,
                          d.name AS deal_name
                   FROM nx_plan p
                   LEFT JOIN nx_client c ON p.client_id = c.id
                   LEFT JOIN nx_deal d ON p.deal_id = d.id
                   WHERE p.id = %s""",
                (plan_id,),
            )
            return row_to_dict(cur)


def get_all_plans(
    plan_type: str | None = None,
    status: str | None = None,
) -> list[dict]:
    clauses = []
    params: list = []
    if plan_type:
        clauses.append("p.plan_type = %s")
        params.append(plan_type)
    if status:
        clauses.append("p.status = %s")
        params.append(status)
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""SELECT p.*,
                           c.name AS client_name,
                           d.name AS deal_name
                    FROM nx_plan p
                    LEFT JOIN nx_client c ON p.client_id = c.id
                    LEFT JOIN nx_deal d ON p.deal_id = d.id
                    {where}
                    ORDER BY p.updated_at DESC""",
                params,
            )
            return rows_to_dicts(cur)


def update_plan(plan_id: int, **fields) -> dict | None:
    if not fields:
        return get_plan(plan_id)
    allowed = {"title", "plan_type", "fiscal_year", "body", "deal_id", "client_id", "notes", "status"}
    filtered = {k: v for k, v in fields.items() if k in allowed}
    if not filtered:
        return get_plan(plan_id)
    sets = ", ".join(f"{k} = %s" for k in filtered)
    vals = list(filtered.values())
    vals.append(plan_id)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""UPDATE nx_plan SET {sets}, updated_at = NOW()
                    WHERE id = %s
                    RETURNING *""",
                vals,
            )
            row = row_to_dict(cur)
    return row


def archive_plan(plan_id: int) -> dict | None:
    return update_plan(plan_id, status="archived")
