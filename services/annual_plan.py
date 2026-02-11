"""Annual plan service — CRUD for annual_plan table (product strategy + quotas).

Public API:
    create(product_id, product_name, ...) → None
    get_all() → list[dict]
    get_by_id(product_id) → dict | None
    update(product_id, ...) → None
    delete(product_id) → None
"""

from database.connection import get_connection


def create(product_id, product_name, quota_fy26=0, strategy=None, target_industry=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO annual_plan (product_id, product_name, quota_fy26, strategy, target_industry)
                   VALUES (%s, %s, %s, %s, %s)""",
                (product_id, product_name, quota_fy26, strategy, target_industry),
            )


def get_all():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM annual_plan ORDER BY product_id")
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_by_id(product_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM annual_plan WHERE product_id = %s", (product_id,))
            row = cur.fetchone()
            if row is None:
                return None
            cols = [d[0] for d in cur.description]
            return dict(zip(cols, row))


def update(product_id, product_name, quota_fy26, strategy, target_industry):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE annual_plan
                   SET product_name = %s, quota_fy26 = %s, strategy = %s,
                       target_industry = %s, updated_at = NOW()
                   WHERE product_id = %s""",
                (product_name, quota_fy26, strategy, target_industry, product_id),
            )


def delete(product_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM annual_plan WHERE product_id = %s", (product_id,))
