"""Nexus subsidy service — CRUD for government grants / subsidies."""

from database.connection import get_connection, row_to_dict, rows_to_dicts

VALID_STAGES = {
    "draft", "evaluating", "applying", "under_review",
    "approved", "rejected", "executing", "completed",
}

ALLOWED_FIELDS = {
    "name", "source", "agency", "program_type", "eligibility",
    "funding_amount", "scope", "required_docs", "deadline", "deadline_date",
    "reference_url", "stage", "client_id", "partner_id", "notes", "status",
}


def create_subsidy(
    name: str,
    program_type: str = "other",
    source: str | None = None,
    agency: str | None = None,
    deadline: str | None = None,
    funding_amount: str | None = None,
    eligibility: str | None = None,
    scope: str | None = None,
    required_docs: str | None = None,
    reference_url: str | None = None,
    client_id: int | None = None,
    partner_id: int | None = None,
    notes: str | None = None,
) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO nx_subsidy
                   (name, program_type, source, agency, deadline, funding_amount,
                    eligibility, scope, required_docs, reference_url, client_id, partner_id, notes)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING *""",
                (name, program_type, source, agency, deadline, funding_amount,
                 eligibility, scope, required_docs, reference_url, client_id, partner_id, notes),
            )
            return row_to_dict(cur)


def get_subsidy(subsidy_id: int) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT s.*,
                          c.name AS client_name,
                          p.name AS partner_name,
                          CASE WHEN s.deadline_date IS NOT NULL
                               THEN CAST(julianday(s.deadline_date) - julianday('now') AS INTEGER)
                          END AS days_left
                   FROM nx_subsidy s
                   LEFT JOIN nx_client c ON s.client_id = c.id
                   LEFT JOIN nx_partner p ON s.partner_id = p.id
                   WHERE s.id = %s""",
                (subsidy_id,),
            )
            return row_to_dict(cur)


def get_all_subsidies(status: str = "active", view: str = "stage") -> list[dict]:
    order = "s.stage ASC, s.created_at DESC"
    if view == "deadline":
        order = "CASE WHEN s.deadline_date IS NULL THEN 1 ELSE 0 END, s.deadline_date ASC"

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""SELECT s.*,
                           c.name AS client_name,
                           p.name AS partner_name,
                           CASE WHEN s.deadline_date IS NOT NULL
                                THEN CAST(julianday(s.deadline_date) - julianday('now') AS INTEGER)
                           END AS days_left
                    FROM nx_subsidy s
                    LEFT JOIN nx_client c ON s.client_id = c.id
                    LEFT JOIN nx_partner p ON s.partner_id = p.id
                    WHERE s.status = %s
                    ORDER BY {order}""",
                (status,),
            )
            return rows_to_dicts(cur)


def get_subsidies_by_client(client_id: int) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT s.*, c.name AS client_name, p.name AS partner_name
                   FROM nx_subsidy s
                   LEFT JOIN nx_client c ON s.client_id = c.id
                   LEFT JOIN nx_partner p ON s.partner_id = p.id
                   WHERE s.client_id = %s
                   ORDER BY s.created_at DESC""",
                (client_id,),
            )
            return rows_to_dicts(cur)


def update_subsidy(subsidy_id: int, **fields) -> dict | None:
    if not fields:
        return get_subsidy(subsidy_id)
    filtered = {k: v for k, v in fields.items() if k in ALLOWED_FIELDS}
    if not filtered:
        return get_subsidy(subsidy_id)
    set_clause = ", ".join(f"{k} = %s" for k in filtered)
    values = list(filtered.values()) + [subsidy_id]
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE nx_subsidy SET {set_clause}, updated_at = datetime('now') WHERE id = %s RETURNING *",
                values,
            )
            return row_to_dict(cur)


def advance_stage(subsidy_id: int, new_stage: str) -> dict | None:
    if new_stage not in VALID_STAGES:
        raise ValueError(f"Invalid stage: {new_stage}")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE nx_subsidy SET stage = %s,
                   updated_at = datetime('now') WHERE id = %s RETURNING *""",
                (new_stage, subsidy_id),
            )
            return row_to_dict(cur)


def close_subsidy(subsidy_id: int, notes: str | None = None) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE nx_subsidy SET status = 'closed',
                   notes = COALESCE(%s, notes),
                   updated_at = datetime('now') WHERE id = %s RETURNING *""",
                (notes, subsidy_id),
            )
            return row_to_dict(cur)


def link_deal(subsidy_id: int, deal_id: int) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO nx_subsidy_deal (subsidy_id, deal_id)
                   VALUES (%s, %s) RETURNING *""",
                (subsidy_id, deal_id),
            )
            return row_to_dict(cur)


def unlink_deal(subsidy_id: int, deal_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM nx_subsidy_deal WHERE subsidy_id = %s AND deal_id = %s",
                (subsidy_id, deal_id),
            )
            return cur._cur.rowcount > 0


def get_subsidy_deals(subsidy_id: int) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT sd.*, d.name AS deal_name, d.stage AS deal_stage,
                          d.status AS deal_status, c.name AS client_name
                   FROM nx_subsidy_deal sd
                   JOIN nx_deal d ON sd.deal_id = d.id
                   JOIN nx_client c ON d.client_id = c.id
                   WHERE sd.subsidy_id = %s
                   ORDER BY d.last_activity_at DESC""",
                (subsidy_id,),
            )
            return rows_to_dicts(cur)


# ---------------------------------------------------------------------------
# Subsidy deadlines (nx_subsidy_deadline)
# ---------------------------------------------------------------------------

ALLOWED_DEADLINE_FIELDS = {"label", "deadline_date", "notes", "status"}


def _sync_deadline_date_with_cursor(subsidy_id: int, cur) -> None:
    """Keep nx_subsidy.deadline_date in sync with nearest open deadline. Uses existing cursor."""
    cur.execute(
        """SELECT deadline_date FROM nx_subsidy_deadline
           WHERE subsidy_id = %s AND status = 'open'
           ORDER BY deadline_date ASC LIMIT 1""",
        (subsidy_id,),
    )
    row = cur.fetchone()
    nearest = row[0] if row else None
    cur.execute(
        "UPDATE nx_subsidy SET deadline_date = %s, updated_at = datetime('now') WHERE id = %s",
        (nearest, subsidy_id),
    )


def add_deadline(
    subsidy_id: int, label: str, deadline_date: str,
    notes: str | None = None, status: str = "open",
) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO nx_subsidy_deadline (subsidy_id, label, deadline_date, notes, status)
                   VALUES (%s, %s, %s, %s, %s) RETURNING *""",
                (subsidy_id, label, deadline_date, notes, status),
            )
            result = row_to_dict(cur)
            _sync_deadline_date_with_cursor(subsidy_id, cur)
            return result


def get_deadlines(subsidy_id: int) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT *,
                          CAST(julianday(deadline_date) - julianday('now') AS INTEGER) AS days_left
                   FROM nx_subsidy_deadline
                   WHERE subsidy_id = %s
                   ORDER BY deadline_date ASC""",
                (subsidy_id,),
            )
            return rows_to_dicts(cur)


def update_deadline(deadline_id: int, **fields) -> dict | None:
    filtered = {k: v for k, v in fields.items() if k in ALLOWED_DEADLINE_FIELDS}
    if not filtered:
        return None
    set_clause = ", ".join(f"{k} = %s" for k in filtered)
    values = list(filtered.values()) + [deadline_id]
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE nx_subsidy_deadline SET {set_clause}, updated_at = datetime('now') WHERE id = %s RETURNING *",
                values,
            )
            result = row_to_dict(cur)
            if result:
                _sync_deadline_date_with_cursor(result["subsidy_id"], cur)
            return result


def delete_deadline(deadline_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT subsidy_id FROM nx_subsidy_deadline WHERE id = %s", (deadline_id,))
            row = cur.fetchone()
            if not row:
                return False
            subsidy_id = row[0]
            cur.execute("DELETE FROM nx_subsidy_deadline WHERE id = %s", (deadline_id,))
            _sync_deadline_date_with_cursor(subsidy_id, cur)
            return True


def get_subsidies_expiring_soon(within_days: int = 30) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT s.*, c.name AS client_name, p.name AS partner_name,
                          CAST(julianday(s.deadline_date) - julianday('now') AS INTEGER) AS days_left
                   FROM nx_subsidy s
                   LEFT JOIN nx_client c ON s.client_id = c.id
                   LEFT JOIN nx_partner p ON s.partner_id = p.id
                   WHERE s.status = 'active'
                     AND s.deadline_date IS NOT NULL
                     AND julianday(s.deadline_date) - julianday('now') <= %s
                     AND julianday(s.deadline_date) - julianday('now') >= 0
                   ORDER BY s.deadline_date ASC""",
                (within_days,),
            )
            return rows_to_dicts(cur)
