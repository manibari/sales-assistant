"""CRUD operations for stage_probability table."""

from database.connection import get_connection


def get_all():
    """Return all stage probabilities ordered by sort_order."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM stage_probability ORDER BY sort_order")
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_by_code(status_code):
    """Return probability for a single status code."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT probability FROM stage_probability WHERE status_code = %s",
                (status_code,),
            )
            row = cur.fetchone()
            return float(row[0]) if row else None


def update(status_code, probability):
    """Update probability for a status code."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE stage_probability
                   SET probability = %s
                   WHERE status_code = %s""",
                (probability, status_code),
            )
