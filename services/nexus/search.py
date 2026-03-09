"""Nexus global search — cross-entity keyword search."""

from database.connection import get_connection, rows_to_dicts


def global_search(query: str, limit: int = 20) -> dict:
    """Search across deals, clients, partners, contacts, and intel."""
    q = f"%{query}%"
    results: dict = {"deals": [], "clients": [], "partners": [], "contacts": [], "intel": []}

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Deals
            cur.execute(
                """SELECT d.id, d.name, d.stage, d.status, c.name AS client_name
                   FROM nx_deal d
                   LEFT JOIN nx_client c ON d.client_id = c.id
                   WHERE d.name LIKE %s OR c.name LIKE %s
                   ORDER BY d.last_activity_at DESC
                   LIMIT %s""",
                (q, q, limit),
            )
            results["deals"] = rows_to_dicts(cur)

            # Clients
            cur.execute(
                """SELECT id, name, industry, status
                   FROM nx_client
                   WHERE name LIKE %s OR industry LIKE %s
                   ORDER BY updated_at DESC
                   LIMIT %s""",
                (q, q, limit),
            )
            results["clients"] = rows_to_dicts(cur)

            # Partners
            cur.execute(
                """SELECT id, name, trust_level
                   FROM nx_partner
                   WHERE name LIKE %s
                   ORDER BY updated_at DESC
                   LIMIT %s""",
                (q, limit),
            )
            results["partners"] = rows_to_dicts(cur)

            # Contacts
            cur.execute(
                """SELECT id, name, title, org_type, org_id
                   FROM nx_contact
                   WHERE name LIKE %s OR title LIKE %s
                   ORDER BY name ASC
                   LIMIT %s""",
                (q, q, limit),
            )
            results["contacts"] = rows_to_dicts(cur)

            # Intel
            cur.execute(
                """SELECT id, raw_input, status, created_at
                   FROM nx_intel
                   WHERE raw_input LIKE %s
                   ORDER BY created_at DESC
                   LIMIT %s""",
                (q, limit),
            )
            results["intel"] = rows_to_dicts(cur)

    return results
