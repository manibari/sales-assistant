"""CRUD operations for sales_plan table."""

from database.connection import get_connection


def create(project_id, product_id=None, expected_invoice_date=None,
           amount=0, confidence_level=0.5, prime_contractor=True, notes=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO sales_plan
                   (project_id, product_id, expected_invoice_date, amount,
                    confidence_level, prime_contractor, notes)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)
                   RETURNING plan_id""",
                (project_id, product_id, expected_invoice_date, amount,
                 confidence_level, prime_contractor, notes),
            )
            return cur.fetchone()[0]


def get_all():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM sales_plan ORDER BY plan_id")
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_by_id(plan_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM sales_plan WHERE plan_id = %s", (plan_id,))
            row = cur.fetchone()
            if row is None:
                return None
            cols = [d[0] for d in cur.description]
            return dict(zip(cols, row))


def update(plan_id, project_id, product_id, expected_invoice_date,
           amount, confidence_level, prime_contractor, notes):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE sales_plan
                   SET project_id = %s, product_id = %s, expected_invoice_date = %s,
                       amount = %s, confidence_level = %s, prime_contractor = %s,
                       notes = %s, updated_at = NOW()
                   WHERE plan_id = %s""",
                (project_id, product_id, expected_invoice_date, amount,
                 confidence_level, prime_contractor, notes, plan_id),
            )


def delete(plan_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM sales_plan WHERE plan_id = %s", (plan_id,))


def get_summary_by_client(client_id):
    """Aggregate revenue metrics for a client: deal_count, total_amount, weighted_amount."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT COUNT(sp.plan_id) AS deal_count,
                          COALESCE(SUM(sp.amount), 0) AS total_amount,
                          COALESCE(SUM(sp.amount * sp.confidence_level), 0) AS weighted_amount
                   FROM sales_plan sp
                   JOIN project_list p ON sp.project_id = p.project_id
                   WHERE p.client_id = %s""",
                (client_id,),
            )
            row = cur.fetchone()
            cols = [d[0] for d in cur.description]
            return dict(zip(cols, row))
