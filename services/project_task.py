"""CRUD + aggregation operations for project_task table."""

from database.connection import get_connection


def create(project_id, task_name, owner=None, status="planned",
           start_date=None, end_date=None, estimated_hours=0,
           actual_hours=0, sort_order=0):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO project_task
                   (project_id, task_name, owner, status, start_date, end_date,
                    estimated_hours, actual_hours, sort_order)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING task_id""",
                (project_id, task_name, owner, status, start_date, end_date,
                 estimated_hours, actual_hours, sort_order),
            )
            return cur.fetchone()[0]


def get_by_project(project_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM project_task WHERE project_id = %s ORDER BY sort_order, task_id",
                (project_id,),
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_by_id(task_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM project_task WHERE task_id = %s", (task_id,))
            row = cur.fetchone()
            if row is None:
                return None
            cols = [d[0] for d in cur.description]
            return dict(zip(cols, row))


def update(task_id, task_name, owner=None, status="planned",
           start_date=None, end_date=None, estimated_hours=0,
           actual_hours=0, sort_order=0):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE project_task
                   SET task_name = %s, owner = %s, status = %s,
                       start_date = %s, end_date = %s,
                       estimated_hours = %s, actual_hours = %s,
                       sort_order = %s, updated_at = NOW()
                   WHERE task_id = %s""",
                (task_name, owner, status, start_date, end_date,
                 estimated_hours, actual_hours, sort_order, task_id),
            )


def delete(task_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM project_task WHERE task_id = %s", (task_id,))


def get_summary(project_id):
    """Aggregate stats: total_tasks, completed_tasks, total_hours, completed_hours."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT
                       COUNT(*) AS total_tasks,
                       COUNT(*) FILTER (WHERE status = 'completed') AS completed_tasks,
                       COALESCE(SUM(estimated_hours), 0) AS total_hours,
                       COALESCE(SUM(actual_hours) FILTER (WHERE status = 'completed'), 0) AS completed_hours
                   FROM project_task
                   WHERE project_id = %s""",
                (project_id,),
            )
            row = cur.fetchone()
            cols = [d[0] for d in cur.description]
            return dict(zip(cols, row))


def get_completed_by_date(project_id):
    """Completed tasks cumulative by date (for burndown chart).

    Returns rows with (completion_date, cumulative_hours) ordered by date.
    Uses updated_at::date as the completion date.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT updated_at::date AS completion_date,
                       SUM(actual_hours) OVER (ORDER BY updated_at::date) AS cumulative_hours
                   FROM project_task
                   WHERE project_id = %s AND status = 'completed'
                   ORDER BY updated_at::date""",
                (project_id,),
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
