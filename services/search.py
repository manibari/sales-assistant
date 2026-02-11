"""Search service — cross-table ILIKE search across contact, crm, project_list.

Public API:
    search_all(query) → dict  # {contacts: [...], clients: [...], projects: [...]}
"""

from database.connection import get_connection


def search_all(query):
    """Search across contacts, clients, and projects. Returns grouped results."""
    pattern = f"%{query}%"
    results = {"contacts": [], "clients": [], "projects": []}

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Search contacts
            cur.execute(
                """SELECT contact_id, name, title, email, phone
                   FROM contact
                   WHERE name ILIKE %s OR email ILIKE %s OR phone ILIKE %s
                         OR title ILIKE %s
                   ORDER BY name
                   LIMIT 50""",
                (pattern, pattern, pattern, pattern),
            )
            cols = [d[0] for d in cur.description]
            results["contacts"] = [dict(zip(cols, row)) for row in cur.fetchall()]

            # Search clients (crm)
            cur.execute(
                """SELECT client_id, company_name, industry, department
                   FROM crm
                   WHERE company_name ILIKE %s OR client_id ILIKE %s
                         OR industry ILIKE %s OR department ILIKE %s
                   ORDER BY company_name
                   LIMIT 50""",
                (pattern, pattern, pattern, pattern),
            )
            cols = [d[0] for d in cur.description]
            results["clients"] = [dict(zip(cols, row)) for row in cur.fetchall()]

            # Search projects
            cur.execute(
                """SELECT p.project_id, p.project_name, p.status_code,
                          p.presale_owner, p.sales_owner, p.postsale_owner,
                          c.company_name AS client_name
                   FROM project_list p
                   LEFT JOIN crm c ON p.client_id = c.client_id
                   WHERE p.project_name ILIKE %s OR p.presale_owner ILIKE %s
                         OR p.sales_owner ILIKE %s OR p.postsale_owner ILIKE %s
                   ORDER BY p.project_id
                   LIMIT 50""",
                (pattern, pattern, pattern, pattern),
            )
            cols = [d[0] for d in cur.description]
            results["projects"] = [dict(zip(cols, row)) for row in cur.fetchall()]

    return results
