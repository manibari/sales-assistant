"""Project service — CRUD + state machine + contact linking for project_list.

Public API:
    create(...) → project_id
    get_all() → list[dict]
    get_by_id(project_id) → dict | None
    get_presale() → list[dict]      # L0-L7, LOST, HOLD
    get_postsale() → list[dict]     # P0-P2
    get_closed() → list[dict]       # P2, LOST, HOLD (with client info)
    update(project_id, ...) → None
    delete(project_id) → None
    transition_status(project_id, new_status) → None  # raises ValueError
    link_contact(project_id, contact_id, role) → None
    unlink_contact(project_id, contact_id) → None
    get_contacts(project_id) → list[dict]
"""

from constants import PRESALE_STATUS_CODES, POSTSALE_STATUS_CODES, VALID_TRANSITIONS
from database.connection import get_connection


def create(project_name, client_id=None, product_id=None, status_code="L0",
           presale_owner=None, postsale_owner=None, sales_owner=None, priority="Medium"):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO project_list
                   (project_name, client_id, product_id, status_code,
                    presale_owner, sales_owner, postsale_owner, priority)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING project_id""",
                (project_name, client_id, product_id, status_code,
                 presale_owner, sales_owner, postsale_owner, priority),
            )
            return cur.fetchone()[0]


def get_all():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM project_list ORDER BY project_id")
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_by_id(project_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM project_list WHERE project_id = %s", (project_id,))
            row = cur.fetchone()
            if row is None:
                return None
            cols = [d[0] for d in cur.description]
            return dict(zip(cols, row))


def get_presale():
    """Get projects in pre-sale stages (L0-L7, LOST, HOLD)."""
    presale_codes = list(PRESALE_STATUS_CODES.keys()) + ["LOST", "HOLD"]
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM project_list WHERE status_code = ANY(%s) ORDER BY project_id",
                (presale_codes,),
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_postsale():
    """Get projects in post-sale stages (P0-P2)."""
    postsale_codes = list(POSTSALE_STATUS_CODES.keys())
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM project_list WHERE status_code = ANY(%s) ORDER BY project_id",
                (postsale_codes,),
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_closed():
    """Get projects in closed states (P2, LOST, HOLD) with client info."""
    closed_codes = ["P2", "LOST", "HOLD"]
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT p.*, c.company_name, c.department,
                          c.decision_maker, c.champions, c.industry
                   FROM project_list p
                   LEFT JOIN crm c ON p.client_id = c.client_id
                   WHERE p.status_code = ANY(%s)
                   ORDER BY c.company_name, p.project_id""",
                (closed_codes,),
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def update(project_id, project_name, client_id, product_id,
           presale_owner, postsale_owner, priority, sales_owner=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE project_list
                   SET project_name = %s, client_id = %s, product_id = %s,
                       presale_owner = %s, sales_owner = %s, postsale_owner = %s,
                       priority = %s, updated_at = NOW()
                   WHERE project_id = %s""",
                (project_name, client_id, product_id,
                 presale_owner, sales_owner, postsale_owner, priority, project_id),
            )


def delete(project_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM project_list WHERE project_id = %s", (project_id,))


def transition_status(project_id, new_status):
    """Transition project status. Raises ValueError if transition is illegal."""
    project = get_by_id(project_id)
    if project is None:
        raise ValueError(f"Project {project_id} not found")

    current = project["status_code"]
    allowed = VALID_TRANSITIONS.get(current, [])

    if new_status not in allowed:
        raise ValueError(
            f"Cannot transition from {current} to {new_status}. "
            f"Allowed: {allowed}"
        )

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE project_list
                   SET status_code = %s, status_updated_at = NOW(), updated_at = NOW()
                   WHERE project_id = %s""",
                (new_status, project_id),
            )

            # Auto-chain: L7 (簽約) automatically transitions to P0 (售後規劃)
            if new_status == "L7":
                cur.execute(
                    """UPDATE project_list
                       SET status_code = 'P0', status_updated_at = NOW(), updated_at = NOW()
                       WHERE project_id = %s""",
                    (project_id,),
                )


def link_contact(project_id, contact_id, role="participant"):
    """Link a contact to a project."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO project_contact (project_id, contact_id, role)
                   VALUES (%s, %s, %s)
                   ON CONFLICT (project_id, contact_id) DO UPDATE SET role = %s""",
                (project_id, contact_id, role, role),
            )


def unlink_contact(project_id, contact_id):
    """Remove a contact from a project."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM project_contact WHERE project_id = %s AND contact_id = %s",
                (project_id, contact_id),
            )


def get_contacts(project_id):
    """Get all contacts linked to a project."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT c.*, pc.role
                   FROM contact c
                   JOIN project_contact pc ON c.contact_id = pc.contact_id
                   WHERE pc.project_id = %s
                   ORDER BY c.name""",
                (project_id,),
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
