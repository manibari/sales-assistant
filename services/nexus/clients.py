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
    # Auto-sync to memory md
    try:
        from services.nexus.memory import sync_from_client
        sync_from_client(client["id"])
    except Exception:
        pass
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
                cur.execute("""SELECT c.*,
                              (SELECT SUM(d.budget_amount)
                               FROM nx_deal d
                               WHERE d.client_id = c.id AND d.status = 'active') AS deal_budget_total
                       FROM nx_client c ORDER BY c.updated_at DESC""")
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
    """Fuzzy match client by name or aliases. Bidirectional substring matching.

    Matches if:
    - DB name contains search name (e.g. DB "先啟資訊系統股份有限公司" matches search "先啟資訊")
    - Search name contains DB name (e.g. search "先啟資訊系統(股)公司 SABRE..." matches DB "先啟資訊")
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            q = f"%{name}%"
            cur.execute(
                """SELECT id, name, industry, status, aliases
                   FROM nx_client
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


def delete_client(client_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM nx_client WHERE id = %s", (client_id,))
            return cur.rowcount > 0


def merge_clients(target_id: int, source_ids: list[int]) -> dict:
    """Merge source clients into target. Moves all FK references, dedup NDA/MOU, deletes sources."""
    if target_id in source_ids:
        return {"error": "target_id cannot be in source_ids"}

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Verify target exists
            cur.execute("SELECT id, name FROM nx_client WHERE id = %s", (target_id,))
            target = cur.fetchone()
            if not target:
                return {"error": f"Target client {target_id} not found"}

            placeholders = ",".join(["%s"] * len(source_ids))
            src_tuple = tuple(source_ids)

            # Move contacts (dedup by email)
            cur.execute(
                f"""UPDATE nx_contact SET org_id = %s
                    WHERE org_type = 'client' AND org_id IN ({placeholders})
                    AND (email IS NULL OR email NOT IN (
                        SELECT email FROM nx_contact WHERE org_type = 'client' AND org_id = %s AND email IS NOT NULL
                    ))""",
                (target_id, *src_tuple, target_id),
            )
            contacts_moved = cur.rowcount
            # Delete remaining duplicate contacts
            cur.execute(
                f"DELETE FROM nx_contact WHERE org_type = 'client' AND org_id IN ({placeholders})",
                src_tuple,
            )

            # Move documents (keep only 1 NDA + 1 MOU for target)
            cur.execute(
                f"DELETE FROM nx_document WHERE client_id IN ({placeholders})",
                src_tuple,
            )

            # Move deals
            cur.execute(
                f"UPDATE nx_deal SET client_id = %s WHERE client_id IN ({placeholders})",
                (target_id, *src_tuple),
            )
            deals_moved = cur.rowcount

            # Move intel entity links (avoid duplicates)
            cur.execute(
                f"""INSERT INTO nx_intel_entity (intel_id, entity_type, entity_id)
                    SELECT intel_id, 'client', %s FROM nx_intel_entity
                    WHERE entity_type = 'client' AND entity_id IN ({placeholders})
                    AND intel_id NOT IN (
                        SELECT intel_id FROM nx_intel_entity WHERE entity_type = 'client' AND entity_id = %s
                    )
                    ON CONFLICT DO NOTHING""",
                (target_id, *src_tuple, target_id),
            )
            cur.execute(
                f"DELETE FROM nx_intel_entity WHERE entity_type = 'client' AND entity_id IN ({placeholders})",
                src_tuple,
            )

            # Move tags (avoid duplicates)
            cur.execute(
                f"""INSERT INTO nx_entity_tag (entity_type, entity_id, tag_id)
                    SELECT 'client', %s, tag_id FROM nx_entity_tag
                    WHERE entity_type = 'client' AND entity_id IN ({placeholders})
                    ON CONFLICT DO NOTHING""",
                (target_id, *src_tuple),
            )
            cur.execute(
                f"DELETE FROM nx_entity_tag WHERE entity_type = 'client' AND entity_id IN ({placeholders})",
                src_tuple,
            )

            # Delete source clients
            cur.execute(
                f"DELETE FROM nx_client WHERE id IN ({placeholders})",
                src_tuple,
            )
            deleted = cur.rowcount

        conn.commit()

    return {
        "target_id": target_id,
        "target_name": target[1],
        "merged": deleted,
        "contacts_moved": contacts_moved,
        "deals_moved": deals_moved,
    }
