"""CRUD operations for work_log table."""

from database.connection import get_connection


def create(project_id, action_type, log_date=None, content=None,
           duration_hours=1.0, source="manual", ref_id=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO work_log
                   (project_id, log_date, action_type, content, duration_hours, source, ref_id)
                   VALUES (%s, COALESCE(%s, CURRENT_DATE), %s, %s, %s, %s, %s)
                   RETURNING log_id""",
                (project_id, log_date, action_type, content, duration_hours, source, ref_id),
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
