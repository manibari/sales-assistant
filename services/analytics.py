"""Analytics Service — Calculations for the War Room Dashboard.

Public API:
    get_manpower_by_initiative() -> dict[str, float]
    get_potential_pipeline_by_initiative() -> dict[str, float]
"""
from collections import defaultdict
from database.connection import get_connection


def get_manpower_by_initiative():
    """
    Calculates the total work_log hours for each strategic initiative.

    Traverses the relationship: work_log -> project_list -> annual_plan
    
    Returns:
        A dictionary mapping product_id (initiative_id) to total hours.
    """
    query = """
        SELECT
            ap.product_id,
            SUM(wl.duration_hours) AS total_hours
        FROM
            annual_plan ap
        JOIN
            project_list pl ON ap.product_id = pl.product_id
        JOIN
            work_log wl ON pl.project_id = wl.project_id
        GROUP BY
            ap.product_id;
    """
    manpower_map = defaultdict(float)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            for row in cur.fetchall():
                product_id, total_hours = row
                manpower_map[product_id] = float(total_hours)
    return manpower_map


def get_potential_pipeline_by_initiative():
    """
    Calculates the total potential sales amount for each strategic initiative.
    
    This only includes projects that are not yet Closed/Won (status < 'L7').

    Traverses the relationship: sales_plan -> project_list -> annual_plan

    Returns:
        A dictionary mapping product_id (initiative_id) to total potential amount.
    """
    query = """
        SELECT
            ap.product_id,
            SUM(sp.amount) AS total_amount
        FROM
            annual_plan ap
        JOIN
            project_list pl ON ap.product_id = pl.product_id
        JOIN
            sales_plan sp ON pl.project_id = sp.project_id
        WHERE
            pl.status_code < 'L7' -- Exclude closed/won deals from "potential"
        GROUP BY
            ap.product_id;
    """
    pipeline_map = defaultdict(float)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            for row in cur.fetchall():
                product_id, total_amount = row
                pipeline_map[product_id] = float(total_amount)
    return pipeline_map
