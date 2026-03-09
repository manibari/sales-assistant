"""Nexus client service — CRUD for client organizations."""

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
            cur.execute("SELECT * FROM nx_client WHERE id = %s", (client_id,))
            return row_to_dict(cur)


def get_all_clients(status: str | None = None) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            if status:
                cur.execute(
                    "SELECT * FROM nx_client WHERE status = %s ORDER BY updated_at DESC",
                    (status,),
                )
            else:
                cur.execute("SELECT * FROM nx_client ORDER BY updated_at DESC")
            return rows_to_dicts(cur)


def update_client(client_id: int, **fields) -> dict | None:
    if not fields:
        return get_client(client_id)
    allowed = {"name", "industry", "budget_range", "status", "notes"}
    filtered = {k: v for k, v in fields.items() if k in allowed}
    if not filtered:
        return get_client(client_id)
    set_clause = ", ".join(f"{k} = %s" for k in filtered)
    values = list(filtered.values()) + [client_id]
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE nx_client SET {set_clause}, updated_at = datetime('now') WHERE id = %s RETURNING *",
                values,
            )
            return row_to_dict(cur)


def delete_client(client_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM nx_client WHERE id = %s", (client_id,))
            return cur._cur.rowcount > 0
