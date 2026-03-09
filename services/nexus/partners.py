"""Nexus partner service — CRUD for partner organizations."""

from database.connection import get_connection, row_to_dict, rows_to_dicts

VALID_TRUST_LEVELS = {"unverified", "testing", "verified", "core_team", "si_backed", "demoted"}


def create_partner(
    name: str,
    trust_level: str = "unverified",
    team_size: str | None = None,
    notes: str | None = None,
) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO nx_partner (name, trust_level, team_size, notes)
                   VALUES (%s, %s, %s, %s)
                   RETURNING *""",
                (name, trust_level, team_size, notes),
            )
            return row_to_dict(cur)


def get_partner(partner_id: int) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM nx_partner WHERE id = %s", (partner_id,))
            return row_to_dict(cur)


def get_all_partners(trust_level: str | None = None) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            if trust_level:
                cur.execute(
                    "SELECT * FROM nx_partner WHERE trust_level = %s ORDER BY updated_at DESC",
                    (trust_level,),
                )
            else:
                cur.execute("SELECT * FROM nx_partner ORDER BY updated_at DESC")
            return rows_to_dicts(cur)


def update_partner(partner_id: int, **fields) -> dict | None:
    if not fields:
        return get_partner(partner_id)
    allowed = {"name", "trust_level", "team_size", "notes"}
    filtered = {k: v for k, v in fields.items() if k in allowed}
    if not filtered:
        return get_partner(partner_id)
    set_clause = ", ".join(f"{k} = %s" for k in filtered)
    values = list(filtered.values()) + [partner_id]
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE nx_partner SET {set_clause}, updated_at = datetime('now') WHERE id = %s RETURNING *",
                values,
            )
            return row_to_dict(cur)


def update_trust_level(partner_id: int, new_level: str) -> dict | None:
    if new_level not in VALID_TRUST_LEVELS:
        raise ValueError(f"Invalid trust level: {new_level}. Must be one of {VALID_TRUST_LEVELS}")
    return update_partner(partner_id, trust_level=new_level)


def delete_partner(partner_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM nx_partner WHERE id = %s", (partner_id,))
            return cur._cur.rowcount > 0
