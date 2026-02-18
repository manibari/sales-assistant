"""Stage probability service — CRUD for stage_probability table.

Per-stage default win probabilities (L0=5%...L7=100%). Used by sales_plan.py
for confidence prefill and pipeline.py for weighted revenue forecast.

Public API:
    get_all() → list[dict]
    get_by_code(status_code) → float | None
    update(status_code, probability) → None
"""

from database.connection import get_connection, rows_to_dicts


def get_all():
    """Return all stage probabilities ordered by sort_order."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM stage_probability ORDER BY sort_order")
            return rows_to_dicts(cur)


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
