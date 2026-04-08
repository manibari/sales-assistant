"""Nexus partner service — CRUD for partner organizations."""

from database.connection import get_connection, row_to_dict, rows_to_dicts

VALID_TRUST_LEVELS = {
    "unverified",
    "testing",
    "verified",
    "core_team",
    "si_backed",
    "demoted",
}


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
            where = "WHERE trust_level = %s" if trust_level else ""
            params: tuple = (trust_level,) if trust_level else ()
            cur.execute(
                f"""SELECT p.*,
                           (SELECT COUNT(*) FROM nx_deal_partner dp
                            JOIN nx_deal d ON dp.deal_id = d.id
                            WHERE dp.partner_id = p.id AND d.status = 'active') AS deal_count
                    FROM nx_partner p {where}
                    ORDER BY p.pinned DESC,
                             (SELECT COUNT(*) FROM nx_deal_partner dp
                              JOIN nx_deal d ON dp.deal_id = d.id
                              WHERE dp.partner_id = p.id AND d.status = 'active') DESC,
                             p.updated_at DESC""",
                params,
            )
            partners = rows_to_dicts(cur)

            if not partners:
                return partners

            # Batch-fetch tags to avoid N+1
            partner_ids = [p["id"] for p in partners]
            cur.execute(
                """SELECT et.entity_id, t.id, t.name, t.category
                   FROM nx_entity_tag et
                   JOIN nx_tag t ON t.id = et.tag_id
                   WHERE et.entity_type = 'partner' AND et.entity_id = ANY(%s)""",
                (partner_ids,),
            )
            tags_by_partner: dict[int, list[dict]] = {}
            for row in cur.fetchall():
                pid = row[0]
                tags_by_partner.setdefault(pid, []).append({"id": row[1], "name": row[2], "category": row[3]})

            for p in partners:
                p["tags"] = tags_by_partner.get(p["id"], [])

            return partners


def update_partner(partner_id: int, **fields) -> dict | None:
    if not fields:
        return get_partner(partner_id)
    allowed = {"name", "trust_level", "team_size", "notes", "aliases", "pinned"}
    filtered = {k: v for k, v in fields.items() if k in allowed}
    if not filtered:
        return get_partner(partner_id)
    set_clause = ", ".join(f"{k} = %s" for k in filtered)
    values = list(filtered.values()) + [partner_id]
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE nx_partner SET {set_clause}, updated_at = NOW() WHERE id = %s RETURNING *",
                values,
            )
            return row_to_dict(cur)


def update_trust_level(partner_id: int, new_level: str) -> dict | None:
    if new_level not in VALID_TRUST_LEVELS:
        raise ValueError(
            f"Invalid trust level: {new_level}. Must be one of {VALID_TRUST_LEVELS}"
        )
    return update_partner(partner_id, trust_level=new_level)


def find_partner_by_name(name: str) -> list[dict]:
    """Fuzzy match partner by name or aliases. Bidirectional substring matching."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            q = f"%{name}%"
            cur.execute(
                """SELECT id, name, trust_level, team_size, aliases
                   FROM nx_partner
                   WHERE name LIKE %s OR aliases LIKE %s
                      OR %s LIKE '%%' || name || '%%'
                      OR %s LIKE '%%' || aliases || '%%'
                   ORDER BY
                     CASE
                       WHEN LOWER(name) = LOWER(%s) THEN 0
                       WHEN LOWER(name) LIKE LOWER(%s) THEN 1
                       WHEN %s LIKE '%%' || LOWER(name) || '%%' THEN 2
                       ELSE 3
                     END,
                     updated_at DESC""",
                (q, q, name, name, name, q, name.lower()),
            )
            return rows_to_dicts(cur)


def toggle_pin_partner(partner_id: int) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE nx_partner SET pinned = NOT pinned, updated_at = NOW() WHERE id = %s RETURNING *",
                (partner_id,),
            )
            return row_to_dict(cur)


def delete_partner(partner_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM nx_partner WHERE id = %s", (partner_id,))
            return cur.rowcount > 0
