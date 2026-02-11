"""CRUD operations for work_log table.
Supports both project-level and client-level activities (S14)."""

from database.connection import get_connection


def create(project_id=None, action_type=None, log_date=None, content=None,
           duration_hours=1.0, source="manual", ref_id=None, client_id=None):
    """Create a work log entry. Either project_id or client_id must be provided."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO work_log
                   (project_id, client_id, log_date, action_type, content,
                    duration_hours, source, ref_id)
                   VALUES (%s, %s, COALESCE(%s, CURRENT_DATE), %s, %s, %s, %s, %s)
                   RETURNING log_id""",
                (project_id, client_id, log_date, action_type, content,
                 duration_hours, source, ref_id),
            )
            return cur.fetchone()[0]


def get_by_project(project_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM work_log WHERE project_id = %s ORDER BY log_date DESC, created_at DESC",
                (project_id,),
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_recent(limit=5):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM work_log ORDER BY created_at DESC LIMIT %s",
                (limit,),
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_by_client(client_id, limit=20):
    """Get all work logs for a client — both project-level and client-level (UNION)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT * FROM (
                       SELECT w.*, p.project_name, 'project' AS log_scope
                       FROM work_log w
                       JOIN project_list p ON w.project_id = p.project_id
                       WHERE p.client_id = %s
                     UNION ALL
                       SELECT w.*, NULL AS project_name, 'client' AS log_scope
                       FROM work_log w
                       WHERE w.client_id = %s AND w.project_id IS NULL
                   ) combined
                   ORDER BY log_date DESC, created_at DESC
                   LIMIT %s""",
                (client_id, client_id, limit),
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_client_only(client_id, limit=20):
    """Get only client-level logs (not tied to a project)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT w.*
                   FROM work_log w
                   WHERE w.client_id = %s AND w.project_id IS NULL
                   ORDER BY w.log_date DESC, w.created_at DESC
                   LIMIT %s""",
                (client_id, limit),
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
