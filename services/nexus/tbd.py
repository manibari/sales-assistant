"""Nexus TBD service — skipped Q&A items + meeting action items."""

from database.connection import get_connection, row_to_dict, rows_to_dicts


def create_tbd(
    question: str,
    linked_type: str | None = None,
    linked_id: int | None = None,
    source: str = "skip",
    context: str | None = None,
) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO nx_tbd_item (question, linked_type, linked_id, source, context)
                   VALUES (%s, %s, %s, %s, %s)
                   RETURNING *""",
                (question, linked_type, linked_id, source, context),
            )
            return row_to_dict(cur)


def get_tbd(tbd_id: int) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM nx_tbd_item WHERE id = %s", (tbd_id,))
            return row_to_dict(cur)


def get_open_tbds(
    linked_type: str | None = None, linked_id: int | None = None
) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            if linked_type and linked_id:
                cur.execute(
                    """SELECT * FROM nx_tbd_item
                       WHERE linked_type = %s AND linked_id = %s AND resolved = FALSE
                       ORDER BY created_at ASC""",
                    (linked_type, linked_id),
                )
            else:
                cur.execute(
                    "SELECT * FROM nx_tbd_item WHERE resolved = FALSE ORDER BY created_at ASC"
                )
            return rows_to_dicts(cur)


def get_all_tbds(include_resolved: bool = False) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            if include_resolved:
                cur.execute(
                    "SELECT * FROM nx_tbd_item ORDER BY resolved, created_at ASC"
                )
            else:
                cur.execute(
                    "SELECT * FROM nx_tbd_item WHERE resolved = FALSE ORDER BY created_at ASC"
                )
            return rows_to_dicts(cur)


def resolve_tbd(tbd_id: int) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE nx_tbd_item SET resolved = TRUE, resolved_at = NOW()
                   WHERE id = %s RETURNING *""",
                (tbd_id,),
            )
            return row_to_dict(cur)


def get_stale_tbds(older_than_days: int = 7) -> list[dict]:
    """Get TBDs that have been open for more than N days."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT * FROM nx_tbd_item
                   WHERE resolved = FALSE
                     AND EXTRACT(DAY FROM NOW() - created_at) > %s
                   ORDER BY created_at ASC""",
                (older_than_days,),
            )
            return rows_to_dicts(cur)


def delete_tbd(tbd_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM nx_tbd_item WHERE id = %s", (tbd_id,))
            return cur.rowcount > 0
