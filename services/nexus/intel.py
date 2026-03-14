"""Nexus intel service — CRUD for intelligence entries."""

from database.connection import get_connection, row_to_dict, rows_to_dicts


def _table_has_column(cur, table_name: str, column_name: str) -> bool:
    """Return True when the SQLite table exists and contains the column."""
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = %s",
        (table_name,),
    )
    if cur.fetchone() is None:
        return False

    cur.execute(f"PRAGMA table_info({table_name})")
    return any(row[1] == column_name for row in cur.fetchall())


def create_intel(
    raw_input: str,
    title: str | None = None,
    input_type: str = "text",
    parsed_json: str | None = None,
    source_contact_id: int | None = None,
) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO nx_intel (title, raw_input, input_type, parsed_json, source_contact_id)
                   VALUES (%s, %s, %s, %s, %s)
                   RETURNING *""",
                (title, raw_input, input_type, parsed_json, source_contact_id),
            )
            return row_to_dict(cur)


def get_intel(intel_id: int) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM nx_intel WHERE id = %s", (intel_id,))
            return row_to_dict(cur)


def get_intel_by_ids(intel_ids: list[int]) -> list[dict]:
    if not intel_ids:
        return []
    with get_connection() as conn:
        with conn.cursor() as cur:
            placeholders = ",".join(["%s"] * len(intel_ids))
            cur.execute(
                f"SELECT * FROM nx_intel WHERE id IN ({placeholders}) ORDER BY created_at DESC",
                intel_ids,
            )
            return rows_to_dicts(cur)


def get_all_intel(status: str | None = None, limit: int = 50) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            if status:
                cur.execute(
                    """SELECT i.*,
                              (SELECT COUNT(*) FROM nx_file f WHERE f.intel_id = i.id) AS file_count
                       FROM nx_intel i
                       WHERE i.status = %s
                       ORDER BY i.created_at DESC LIMIT %s""",
                    (status, limit),
                )
            else:
                cur.execute(
                    """SELECT i.*,
                              (SELECT COUNT(*) FROM nx_file f WHERE f.intel_id = i.id) AS file_count
                       FROM nx_intel i
                       ORDER BY i.created_at DESC LIMIT %s""",
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
    allowed = {"title", "raw_input", "input_type", "parsed_json", "chat_history", "status", "source_contact_id"}
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


def get_intel_linked_deals(intel_id: int) -> list[dict]:
    """Get deals linked to this intel via nx_deal_intel."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT d.id, d.name, d.stage, d.status, c.name AS client_name
                   FROM nx_deal_intel di
                   JOIN nx_deal d ON di.deal_id = d.id
                   JOIN nx_client c ON d.client_id = c.id
                   WHERE di.intel_id = %s""",
                (intel_id,),
            )
            return rows_to_dicts(cur)


def delete_intel(intel_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Clean up references first so older local DBs do not trip over
            # missing tables/columns while we migrate schema forward.
            cleanup_targets = [
                ("nx_deal_intel", "intel_id"),
                ("nx_intel_entity", "intel_id"),
                ("nx_intel_field", "intel_id"),
                ("nx_file", "intel_id"),
            ]
            for table_name, column_name in cleanup_targets:
                if _table_has_column(cur, table_name, column_name):
                    cur.execute(
                        f"DELETE FROM {table_name} WHERE {column_name} = %s",
                        (intel_id,),
                    )
            cur.execute("DELETE FROM nx_intel WHERE id = %s", (intel_id,))
            return cur._cur.rowcount > 0


# ---------------------------------------------------------------------------
# Intel ↔ Entity linking (nx_intel_entity)
# ---------------------------------------------------------------------------

def link_intel_entity(
    intel_id: int, entity_type: str, entity_id: int, relation: str = "mentioned"
) -> dict | None:
    """Link an intel to an entity. INSERT OR IGNORE for idempotency."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT OR IGNORE INTO nx_intel_entity (intel_id, entity_type, entity_id, relation)
                   VALUES (%s, %s, %s, %s)""",
                (intel_id, entity_type, entity_id, relation),
            )
            # Return the row (may already exist)
            cur.execute(
                """SELECT * FROM nx_intel_entity
                   WHERE intel_id = %s AND entity_type = %s AND entity_id = %s""",
                (intel_id, entity_type, entity_id),
            )
            return row_to_dict(cur)


def get_intel_entities(intel_id: int) -> list[dict]:
    """Get all entities linked to an intel."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT ie.*,
                          CASE ie.entity_type
                            WHEN 'client' THEN (SELECT name FROM nx_client WHERE id = ie.entity_id)
                            WHEN 'partner' THEN (SELECT name FROM nx_partner WHERE id = ie.entity_id)
                            WHEN 'contact' THEN (SELECT name FROM nx_contact WHERE id = ie.entity_id)
                            WHEN 'deal' THEN (SELECT name FROM nx_deal WHERE id = ie.entity_id)
                          END AS entity_name
                   FROM nx_intel_entity ie
                   WHERE ie.intel_id = %s
                   ORDER BY ie.entity_type, ie.entity_id""",
                (intel_id,),
            )
            return rows_to_dicts(cur)


def get_entity_intel(entity_type: str, entity_id: int) -> list[dict]:
    """Get all intel linked to a specific entity."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT i.*, ie.relation
                   FROM nx_intel_entity ie
                   JOIN nx_intel i ON ie.intel_id = i.id
                   WHERE ie.entity_type = %s AND ie.entity_id = %s
                   ORDER BY i.created_at DESC""",
                (entity_type, entity_id),
            )
            return rows_to_dicts(cur)


# ---------------------------------------------------------------------------
# Intel field index (nx_intel_field)
# ---------------------------------------------------------------------------

def materialize_intel_fields(intel_id: int, parsed: dict) -> int:
    """Flatten parsed_json into nx_intel_field rows. Returns count of fields indexed.

    Idempotent: deletes existing rows for this intel_id then re-inserts.
    Array values are split into separate rows.
    """
    count = 0
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM nx_intel_field WHERE intel_id = %s", (intel_id,))
            for key, value in parsed.items():
                if value is None:
                    continue
                if isinstance(value, list):
                    for item in value:
                        cur.execute(
                            """INSERT OR IGNORE INTO nx_intel_field (intel_id, field_key, field_value)
                               VALUES (%s, %s, %s)""",
                            (intel_id, key, str(item)),
                        )
                        count += 1
                else:
                    cur.execute(
                        """INSERT OR IGNORE INTO nx_intel_field (intel_id, field_key, field_value)
                           VALUES (%s, %s, %s)""",
                        (intel_id, key, str(value)),
                    )
                    count += 1
    return count
