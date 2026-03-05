"""Network service — CRUD for stakeholder relationships + intelligence leverage.

Public API:
    create_relation(from_id, to_id, relation_type, ...) → id
    get_relations(contact_id) → list[dict]
    get_all_relations() → list[dict]
    delete_relation(relation_id) → None
    create_intel(title, ...) → id
    get_all_intel() → list[dict]
    get_intel_by_id(intel_id) → dict | None
    link_intel_org(intel_id, crm_id) → None
    unlink_intel_org(intel_id, crm_id) → None
    delete_intel(intel_id) → None
    get_graph_data() → dict   # nodes + edges for visualization
"""

from database.connection import get_connection, row_to_dict, rows_to_dicts


# --- Stakeholder Relations ---

def create_relation(
    from_contact_id: int,
    to_contact_id: int,
    relation_type: str,
    notes: str | None = None,
    leverage_value: str = "medium",
) -> int:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO stakeholder_relation
                   (from_contact_id, to_contact_id, relation_type, notes, leverage_value)
                   VALUES (%s, %s, %s, %s, %s)
                   RETURNING id""",
                (from_contact_id, to_contact_id, relation_type, notes, leverage_value),
            )
            return cur.fetchone()[0]


def get_relations(contact_id: int) -> list[dict]:
    """Get all relations where contact is either source or target."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT sr.*,
                          cf.name AS from_name, ct.name AS to_name
                   FROM stakeholder_relation sr
                   JOIN contact cf ON sr.from_contact_id = cf.contact_id
                   JOIN contact ct ON sr.to_contact_id = ct.contact_id
                   WHERE sr.from_contact_id = %s OR sr.to_contact_id = %s
                   ORDER BY sr.created_at DESC""",
                (contact_id, contact_id),
            )
            return rows_to_dicts(cur)


def get_all_relations() -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT sr.*,
                          cf.name AS from_name, ct.name AS to_name
                   FROM stakeholder_relation sr
                   JOIN contact cf ON sr.from_contact_id = cf.contact_id
                   JOIN contact ct ON sr.to_contact_id = ct.contact_id
                   ORDER BY sr.created_at DESC"""
            )
            return rows_to_dicts(cur)


def delete_relation(relation_id: int) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM stakeholder_relation WHERE id = %s", (relation_id,))


# --- Intel / Leverage ---

def create_intel(
    title: str,
    summary: str | None = None,
    leverage_value: str = "medium",
    source_contact_id: int | None = None,
    org_ids: list[str] | None = None,
) -> int:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO intel (title, summary, leverage_value, source_contact_id)
                   VALUES (%s, %s, %s, %s)
                   RETURNING id""",
                (title, summary, leverage_value, source_contact_id),
            )
            intel_id = cur.fetchone()[0]
            if org_ids:
                for crm_id in org_ids:
                    cur.execute(
                        """INSERT INTO intel_org (intel_id, crm_id)
                           VALUES (%s, %s)
                           ON CONFLICT DO NOTHING""",
                        (intel_id, crm_id),
                    )
            return intel_id


def get_all_intel() -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Get all intel with source contact name
            cur.execute(
                """SELECT i.*,
                          c.name AS source_contact_name
                   FROM intel i
                   LEFT JOIN contact c ON i.source_contact_id = c.contact_id
                   ORDER BY i.created_at DESC"""
            )
            items = rows_to_dicts(cur)

            # Attach linked orgs to each intel
            for item in items:
                cur.execute(
                    """SELECT io.crm_id, cr.company_name
                       FROM intel_org io
                       JOIN crm cr ON io.crm_id = cr.client_id
                       WHERE io.intel_id = ?""",
                    (item["id"],),
                )
                item["orgs"] = [
                    {"crm_id": r[0], "company_name": r[1]}
                    for r in cur.fetchall()
                ]
            return items


def get_intel_by_id(intel_id: int) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT i.*,
                          c.name AS source_contact_name
                   FROM intel i
                   LEFT JOIN contact c ON i.source_contact_id = c.contact_id
                   WHERE i.id = %s""",
                (intel_id,),
            )
            return row_to_dict(cur)


def link_intel_org(intel_id: int, crm_id: str) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO intel_org (intel_id, crm_id)
                   VALUES (%s, %s)
                   ON CONFLICT DO NOTHING""",
                (intel_id, crm_id),
            )


def unlink_intel_org(intel_id: int, crm_id: str) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM intel_org WHERE intel_id = %s AND crm_id = %s",
                (intel_id, crm_id),
            )


def delete_intel(intel_id: int) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM intel WHERE id = %s", (intel_id,))


# --- Graph Data (for visualization) ---

def get_graph_data() -> dict:
    """
    Build nodes + edges for the relationship network graph.
    Nodes: contacts (person), organizations (org), projects (project)
    Edges: works_at, participates_in, stakeholder_relation types
    """
    nodes = []
    edges = []

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Contacts as person nodes
            cur.execute("SELECT contact_id, name FROM contact")
            for row in cur.fetchall():
                nodes.append({
                    "id": f"contact_{row[0]}",
                    "label": row[1],
                    "type": "person",
                })

            # Organizations as org nodes
            cur.execute("SELECT client_id, company_name FROM crm")
            for row in cur.fetchall():
                nodes.append({
                    "id": f"org_{row[0]}",
                    "label": row[1],
                    "type": "org",
                })

            # Projects as project nodes
            cur.execute(
                """SELECT project_id, project_name, status_code
                   FROM project_list
                   WHERE status_code NOT IN ('LOST', 'HOLD', 'P2')"""
            )
            for row in cur.fetchall():
                nodes.append({
                    "id": f"project_{row[0]}",
                    "label": row[1],
                    "type": "project",
                    "status": row[2],
                })

            # Contact → Org edges (via account_contact)
            cur.execute(
                """SELECT ac.contact_id, ac.client_id, ac.role
                   FROM account_contact ac"""
            )
            for row in cur.fetchall():
                edges.append({
                    "source": f"contact_{row[0]}",
                    "target": f"org_{row[1]}",
                    "type": "works_at",
                    "label": row[2],
                })

            # Contact → Project edges (via project_contact)
            cur.execute(
                """SELECT pc.contact_id, pc.project_id, pc.role
                   FROM project_contact pc"""
            )
            for row in cur.fetchall():
                edges.append({
                    "source": f"contact_{row[0]}",
                    "target": f"project_{row[1]}",
                    "type": "participates_in",
                    "label": row[2],
                })

            # Stakeholder relations (contact → contact)
            cur.execute(
                """SELECT id, from_contact_id, to_contact_id,
                          relation_type, leverage_value
                   FROM stakeholder_relation"""
            )
            for row in cur.fetchall():
                edges.append({
                    "source": f"contact_{row[1]}",
                    "target": f"contact_{row[2]}",
                    "type": row[3],
                    "label": row[3],
                    "leverage": row[4],
                })

            # Intel → Org edges
            cur.execute(
                """SELECT i.id, i.title, io.crm_id, i.leverage_value
                   FROM intel i
                   JOIN intel_org io ON i.id = io.intel_id"""
            )
            for row in cur.fetchall():
                intel_node_id = f"intel_{row[0]}"
                # Add intel node if not already added
                if not any(n["id"] == intel_node_id for n in nodes):
                    nodes.append({
                        "id": intel_node_id,
                        "label": row[1],
                        "type": "intel",
                        "leverage": row[3],
                    })
                edges.append({
                    "source": intel_node_id,
                    "target": f"org_{row[2]}",
                    "type": "intel_leverage",
                    "leverage": row[3],
                })

    return {"nodes": nodes, "edges": edges}
