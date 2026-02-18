"""Annual plan service — CRUD for annual_plan table (product strategy + quotas).

Public API:
    create(product_id, product_name, ...) → None
    get_all() → list[dict]
    get_by_id(product_id) → dict | None
    update(product_id, ...) → None
    delete(product_id) → None
"""

import streamlit as st
from database.connection import get_connection, row_to_dict, rows_to_dicts


def create(
    product_id,
    product_name,
    quota_fy26=0,
    strategy=None,
    target_industry=None,
    pillar=None,
    owner=None,
    kpis=None,
    status="Q2 計劃",
    battlefront=None,
):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO annual_plan (
                       product_id, product_name, quota_fy26, strategy, target_industry,
                       pillar, owner, kpis, status, battlefront
                   )
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    product_id,
                    product_name,
                    quota_fy26,
                    strategy,
                    target_industry,
                    pillar,
                    owner,
                    kpis,
                    status,
                    battlefront,
                ),
            )


@st.cache_data
def get_all():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM annual_plan ORDER BY product_id")
            return rows_to_dicts(cur)


def get_by_id(product_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM annual_plan WHERE product_id = %s", (product_id,))
            return row_to_dict(cur)


def update(
    product_id, product_name, quota_fy26, strategy, target_industry,
    pillar, owner, kpis, status, battlefront
):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE annual_plan
                   SET product_name = %s, quota_fy26 = %s, strategy = %s,
                       target_industry = %s, pillar = %s, owner = %s, kpis = %s,
                       status = %s, battlefront = %s, updated_at = NOW()
                   WHERE product_id = %s""",
                (
                    product_name, quota_fy26, strategy, target_industry,
                    pillar, owner, kpis, status, battlefront, product_id
                ),
            )


def delete(product_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM annual_plan WHERE product_id = %s", (product_id,))
