"""Nexus tag service — universal tags + polymorphic entity tagging."""

from database.connection import get_connection, row_to_dict, rows_to_dicts


def create_tag(name: str, category: str) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO nx_tag (name, category) VALUES (%s, %s)
                   ON CONFLICT(name, category) DO UPDATE SET name = excluded.name
                   RETURNING *""",
                (name, category),
            )
            return row_to_dict(cur)


def get_all_tags(category: str | None = None) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            if category:
                cur.execute(
                    "SELECT * FROM nx_tag WHERE category = %s ORDER BY name",
                    (category,),
                )
            else:
                cur.execute("SELECT * FROM nx_tag ORDER BY category, name")
            return rows_to_dicts(cur)


def tag_entity(entity_type: str, entity_id: int, tag_id: int) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO nx_entity_tag (entity_type, entity_id, tag_id)
                   VALUES (%s, %s, %s)
                   ON CONFLICT(entity_type, entity_id, tag_id) DO UPDATE SET entity_type = excluded.entity_type
                   RETURNING *""",
                (entity_type, entity_id, tag_id),
            )
            return row_to_dict(cur)


def untag_entity(entity_type: str, entity_id: int, tag_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """DELETE FROM nx_entity_tag
                   WHERE entity_type = %s AND entity_id = %s AND tag_id = %s""",
                (entity_type, entity_id, tag_id),
            )
            return cur.rowcount > 0


def get_entity_tags(entity_type: str, entity_id: int) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT t.* FROM nx_tag t
                   JOIN nx_entity_tag et ON t.id = et.tag_id
                   WHERE et.entity_type = %s AND et.entity_id = %s
                   ORDER BY t.category, t.name""",
                (entity_type, entity_id),
            )
            return rows_to_dicts(cur)


def get_entities_by_tag(tag_id: int, entity_type: str | None = None) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            if entity_type:
                cur.execute(
                    """SELECT * FROM nx_entity_tag
                       WHERE tag_id = %s AND entity_type = %s""",
                    (tag_id, entity_type),
                )
            else:
                cur.execute(
                    "SELECT * FROM nx_entity_tag WHERE tag_id = %s",
                    (tag_id,),
                )
            return rows_to_dicts(cur)


def search_by_tag_name(query: str, category: str | None = None) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            if category:
                cur.execute(
                    "SELECT * FROM nx_tag WHERE name LIKE %s AND category = %s ORDER BY name",
                    (f"%{query}%", category),
                )
            else:
                cur.execute(
                    "SELECT * FROM nx_tag WHERE name LIKE %s ORDER BY category, name",
                    (f"%{query}%",),
                )
            return rows_to_dicts(cur)
