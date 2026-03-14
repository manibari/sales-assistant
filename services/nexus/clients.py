"""Nexus client service — CRUD for client organizations."""

import json

from database.connection import get_connection, row_to_dict, rows_to_dicts


def create_client(
    name: str,
    industry: str | None = None,
    budget_range: str | None = None,
    notes: str | None = None,
) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO nx_client (name, industry, budget_range, notes)
                   VALUES (%s, %s, %s, %s)
                   RETURNING *""",
                (name, industry, budget_range, notes),
            )
            client = row_to_dict(cur)
    # Auto-create NDA + MOU tracking entries
    _auto_create_documents(client["id"])
    return client


def _auto_create_documents(client_id: int) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            for doc_type in ("nda", "mou"):
                cur.execute(
                    """INSERT INTO nx_document (client_id, doc_type, status)
                       VALUES (%s, %s, 'pending')""",
                    (client_id, doc_type),
                )


def get_client(client_id: int) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT c.*,
                          (SELECT SUM(d.budget_amount)
                           FROM nx_deal d
                           WHERE d.client_id = c.id AND d.status = 'active') AS deal_budget_total
                   FROM nx_client c WHERE c.id = %s""",
                (client_id,),
            )
            client = row_to_dict(cur)
            if not client:
                return None
            # Add per-year breakdown
            cur.execute(
                """SELECT d.budget_year AS year, SUM(d.budget_amount) AS total
                   FROM nx_deal d
                   WHERE d.client_id = %s AND d.status = 'active' AND d.budget_amount IS NOT NULL
                   GROUP BY d.budget_year
                   ORDER BY d.budget_year""",
                (client_id,),
            )
            client["deal_budgets_by_year"] = rows_to_dicts(cur)
            return client


def get_all_clients(status: str | None = None) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            if status:
                cur.execute(
                    """SELECT c.*,
                              (SELECT SUM(d.budget_amount)
                               FROM nx_deal d
                               WHERE d.client_id = c.id AND d.status = 'active') AS deal_budget_total
                       FROM nx_client c WHERE c.status = %s ORDER BY c.updated_at DESC""",
                    (status,),
                )
            else:
                cur.execute(
                    """SELECT c.*,
                              (SELECT SUM(d.budget_amount)
                               FROM nx_deal d
                               WHERE d.client_id = c.id AND d.status = 'active') AS deal_budget_total
                       FROM nx_client c ORDER BY c.updated_at DESC"""
                )
            return rows_to_dicts(cur)


def update_client(client_id: int, **fields) -> dict | None:
    if not fields:
        return get_client(client_id)
    allowed = {"name", "industry", "budget_range", "status", "notes", "aliases"}
    filtered = {k: v for k, v in fields.items() if k in allowed}
    if not filtered:
        return get_client(client_id)
    set_clause = ", ".join(f"{k} = %s" for k in filtered)
    values = list(filtered.values()) + [client_id]
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE nx_client SET {set_clause}, updated_at = NOW() WHERE id = %s RETURNING *",
                values,
            )
            return row_to_dict(cur)


def find_client_by_name(name: str) -> list[dict]:
    """Fuzzy match client by name or aliases. Returns candidate list sorted by match quality."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            q = f"%{name}%"
            cur.execute(
                """SELECT id, name, industry, status, aliases
                   FROM nx_client
                   WHERE name LIKE %s OR aliases LIKE %s
                   ORDER BY
                     CASE
                       WHEN LOWER(name) = LOWER(%s) THEN 0
                       WHEN LOWER(name) LIKE LOWER(%s) THEN 1
                       ELSE 2
                     END,
                     updated_at DESC""",
                (q, q, name, q),
            )
            return rows_to_dicts(cur)


def delete_client(client_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM nx_client WHERE id = %s", (client_id,))
            return cur.rowcount > 0
