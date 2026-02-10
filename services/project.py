"""CRUD operations + state machine for project_list table."""

from constants import VALID_TRANSITIONS
from database.connection import get_connection


def create(project_name, client_id=None, product_id=None, status_code="S01",
           owner=None, priority="Medium"):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO project_list
                   (project_name, client_id, product_id, status_code, owner, priority)
                   VALUES (%s, %s, %s, %s, %s, %s)
                   RETURNING project_id""",
                (project_name, client_id, product_id, status_code, owner, priority),
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


def update(project_id, project_name, client_id, product_id, owner, priority):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE project_list
                   SET project_name = %s, client_id = %s, product_id = %s,
                       owner = %s, priority = %s, updated_at = NOW()
                   WHERE project_id = %s""",
                (project_name, client_id, product_id, owner, priority, project_id),
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
