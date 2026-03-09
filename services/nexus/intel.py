"""Nexus intel service — CRUD for intelligence entries."""

from database.connection import get_connection, row_to_dict, rows_to_dicts


def create_intel(
    raw_input: str,
    input_type: str = "text",
    parsed_json: str | None = None,
    source_contact_id: int | None = None,
) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO nx_intel (raw_input, input_type, parsed_json, source_contact_id)
                   VALUES (%s, %s, %s, %s)
                   RETURNING *""",
                (raw_input, input_type, parsed_json, source_contact_id),
            )
            return row_to_dict(cur)


def get_intel(intel_id: int) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM nx_intel WHERE id = %s", (intel_id,))
            return row_to_dict(cur)


def get_all_intel(status: str | None = None, limit: int = 50) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            if status:
                cur.execute(
                    "SELECT * FROM nx_intel WHERE status = %s ORDER BY created_at DESC LIMIT %s",
                    (status, limit),
                )
            else:
                cur.execute(
                    "SELECT * FROM nx_intel ORDER BY created_at DESC LIMIT %s",
                    (limit,),
                )
            return rows_to_dicts(cur)


def confirm_intel(intel_id: int, parsed_json: str | None = None) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            if parsed_json:
                cur.execute(
                    """UPDATE nx_intel SET status = 'confirmed', parsed_json = %s,
                       updated_at = datetime('now') WHERE id = %s RETURNING *""",
                    (parsed_json, intel_id),
                )
            else:
                cur.execute(
                    """UPDATE nx_intel SET status = 'confirmed',
                       updated_at = datetime('now') WHERE id = %s RETURNING *""",
                    (intel_id,),
                )
            return row_to_dict(cur)


def update_intel(intel_id: int, **fields) -> dict | None:
    if not fields:
        return get_intel(intel_id)
    allowed = {"raw_input", "input_type", "parsed_json", "status", "source_contact_id"}
    filtered = {k: v for k, v in fields.items() if k in allowed}
    if not filtered:
        return get_intel(intel_id)
    set_clause = ", ".join(f"{k} = %s" for k in filtered)
    values = list(filtered.values()) + [intel_id]
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE nx_intel SET {set_clause}, updated_at = datetime('now') WHERE id = %s RETURNING *",
                values,
            )
            return row_to_dict(cur)


def delete_intel(intel_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM nx_intel WHERE id = %s", (intel_id,))
            return cur._cur.rowcount > 0
