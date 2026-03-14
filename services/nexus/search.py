"""Nexus global search — cross-entity keyword search."""

from database.connection import get_connection, rows_to_dicts


def global_search(query: str, limit: int = 20) -> dict:
    """Search across deals, clients, partners, contacts, intel, and intel fields."""
    q = f"%{query}%"
    results: dict = {
        "deals": [],
        "clients": [],
        "partners": [],
        "contacts": [],
        "intel": [],
        "subsidies": [],
    }

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

            # Clients (includes aliases search)
            cur.execute(
                """SELECT id, name, industry, status
                   FROM nx_client
                   WHERE name LIKE %s OR industry LIKE %s OR aliases LIKE %s
                   ORDER BY updated_at DESC
                   LIMIT %s""",
                (q, q, q, limit),
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

            # Subsidies
            cur.execute(
                """SELECT id, name, agency, program_type, stage, deadline, funding_amount, eligibility, scope, notes, status
                   FROM nx_subsidy
                   WHERE name LIKE %s OR agency LIKE %s OR notes LIKE %s
                         OR eligibility LIKE %s OR scope LIKE %s
                   ORDER BY updated_at DESC
                   LIMIT %s""",
                (q, q, q, q, q, limit),
            )
            results["subsidies"] = rows_to_dicts(cur)

            # Intel — title + raw_input + intel_field values
            cur.execute(
                """SELECT DISTINCT i.id, i.title, i.raw_input, i.status, i.created_at
                   FROM nx_intel i
                   LEFT JOIN nx_intel_field f ON f.intel_id = i.id
                   WHERE i.title LIKE %s OR i.raw_input LIKE %s OR f.field_value LIKE %s
                   ORDER BY i.created_at DESC
                   LIMIT %s""",
                (q, q, q, limit),
            )
            results["intel"] = rows_to_dicts(cur)

    return results


def search_intel_by_field(
    field_key: str, field_value: str, limit: int = 50
) -> list[dict]:
    """Search intel entries by specific field key/value pair."""
    v = f"%{field_value}%"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT i.id, i.title, i.raw_input, i.status, i.created_at,
                          f.field_key, f.field_value
                   FROM nx_intel_field f
                   JOIN nx_intel i ON f.intel_id = i.id
                   WHERE f.field_key = %s AND f.field_value LIKE %s
                   ORDER BY i.created_at DESC
                   LIMIT %s""",
                (field_key, v, limit),
            )
            return rows_to_dicts(cur)
