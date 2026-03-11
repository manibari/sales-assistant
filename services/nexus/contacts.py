"""Nexus contact service — CRUD for people linked to clients or partners."""

from database.connection import get_connection, row_to_dict, rows_to_dicts


def create_contact(
    name: str,
    org_type: str | None = None,
    org_id: int | None = None,
    title: str | None = None,
    phone: str | None = None,
    email: str | None = None,
    line_id: str | None = None,
    role: str | None = None,
    notes: str | None = None,
) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO nx_contact (name, org_type, org_id, title, phone, email, line_id, role, notes)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING *""",
                (name, org_type, org_id, title, phone, email, line_id, role, notes),
            )
            return row_to_dict(cur)


def get_contact(contact_id: int) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM nx_contact WHERE id = %s", (contact_id,))
            return row_to_dict(cur)


def get_contacts_by_org(org_type: str, org_id: int) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM nx_contact WHERE org_type = %s AND org_id = %s ORDER BY name",
                (org_type, org_id),
            )
            return rows_to_dicts(cur)


def get_all_contacts() -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM nx_contact ORDER BY updated_at DESC")
            return rows_to_dicts(cur)


def update_contact(contact_id: int, **fields) -> dict | None:
    if not fields:
        return get_contact(contact_id)
    allowed = {"name", "title", "phone", "email", "line_id", "org_type", "org_id", "role", "notes"}
    filtered = {k: v for k, v in fields.items() if k in allowed}
    if not filtered:
        return get_contact(contact_id)
    set_clause = ", ".join(f"{k} = %s" for k in filtered)
    values = list(filtered.values()) + [contact_id]
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE nx_contact SET {set_clause}, updated_at = datetime('now') WHERE id = %s RETURNING *",
                values,
            )
            return row_to_dict(cur)


def find_contact(name: str | None = None, email: str | None = None) -> list[dict]:
    """Find contacts by name (LIKE) or email (exact). Returns candidate list."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            if email:
                cur.execute(
                    "SELECT * FROM nx_contact WHERE LOWER(email) = LOWER(%s)",
                    (email,),
                )
                results = rows_to_dicts(cur)
                if results:
                    return results
            if name:
                q = f"%{name}%"
                cur.execute(
                    """SELECT * FROM nx_contact WHERE name LIKE %s
                       ORDER BY CASE WHEN LOWER(name) = LOWER(%s) THEN 0 ELSE 1 END,
                               updated_at DESC""",
                    (q, name),
                )
                return rows_to_dicts(cur)
            return []


def delete_contact(contact_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM nx_contact WHERE id = %s", (contact_id,))
            return cur._cur.rowcount > 0
