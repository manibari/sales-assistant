"""Client health score computation (S16).

Score range: 0-100 based on four dimensions:
  - activity_recency (30): days since last interaction
  - activity_frequency (25): activity count in last 90 days
  - deal_value (25): total pipeline amount
  - deal_progress (20): best stage progress
"""

from database.connection import get_connection
from constants import HEALTH_SCORE_WEIGHTS, HEALTH_SCORE_THRESHOLDS


def compute_health_score(client_id):
    """Compute health score (0-100) for a client. Returns dict with score + breakdown."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            breakdown = {}

            # 1. Activity recency: days since last activity (project-level or client-level)
            cur.execute("""
                SELECT MIN(days_ago) FROM (
                    SELECT EXTRACT(DAY FROM NOW() - MAX(w.log_date))::int AS days_ago
                    FROM work_log w
                    JOIN project_list p ON w.project_id = p.project_id
                    WHERE p.client_id = %s
                  UNION ALL
                    SELECT EXTRACT(DAY FROM NOW() - MAX(w.log_date))::int AS days_ago
                    FROM work_log w
                    WHERE w.client_id = %s AND w.project_id IS NULL
                ) sub
            """, (client_id, client_id))
            row = cur.fetchone()
            days_ago = row[0] if row and row[0] is not None else 999

            # ≤7 days = full score, >90 days = 0, linear in between
            if days_ago <= 7:
                recency_pct = 1.0
            elif days_ago >= 90:
                recency_pct = 0.0
            else:
                recency_pct = (90 - days_ago) / (90 - 7)
            breakdown["activity_recency"] = round(recency_pct * HEALTH_SCORE_WEIGHTS["activity_recency"], 1)

            # 2. Activity frequency: count of activities in last 90 days
            cur.execute("""
                SELECT COUNT(*) FROM (
                    SELECT w.log_id FROM work_log w
                    JOIN project_list p ON w.project_id = p.project_id
                    WHERE p.client_id = %s AND w.log_date >= CURRENT_DATE - 90
                  UNION ALL
                    SELECT w.log_id FROM work_log w
                    WHERE w.client_id = %s AND w.project_id IS NULL
                      AND w.log_date >= CURRENT_DATE - 90
                ) sub
            """, (client_id, client_id))
            activity_count = cur.fetchone()[0]

            # 0 activities = 0, ≥10 = full score, linear
            freq_pct = min(activity_count / 10.0, 1.0)
            breakdown["activity_frequency"] = round(freq_pct * HEALTH_SCORE_WEIGHTS["activity_frequency"], 1)

            # 3. Deal value: total pipeline amount
            cur.execute("""
                SELECT COALESCE(SUM(sp.amount), 0)
                FROM sales_plan sp
                JOIN project_list p ON sp.project_id = p.project_id
                WHERE p.client_id = %s
            """, (client_id,))
            total_amount = float(cur.fetchone()[0])

            # 0 = 0, ≥1M = full score, log-scale approximation
            if total_amount <= 0:
                value_pct = 0.0
            elif total_amount >= 1_000_000:
                value_pct = 1.0
            else:
                value_pct = min(total_amount / 1_000_000, 1.0)
            breakdown["deal_value"] = round(value_pct * HEALTH_SCORE_WEIGHTS["deal_value"], 1)

            # 4. Deal progress: best stage among active projects
            cur.execute("""
                SELECT status_code FROM project_list
                WHERE client_id = %s
                ORDER BY
                    CASE
                        WHEN status_code LIKE 'P%%' THEN 100
                        WHEN status_code = 'L7' THEN 90
                        WHEN status_code = 'L6' THEN 80
                        WHEN status_code = 'L5' THEN 70
                        WHEN status_code = 'L4' THEN 60
                        WHEN status_code = 'L3' THEN 50
                        WHEN status_code = 'L2' THEN 40
                        WHEN status_code = 'L1' THEN 30
                        WHEN status_code = 'L0' THEN 20
                        ELSE 0
                    END DESC
                LIMIT 1
            """, (client_id,))
            best_row = cur.fetchone()
            if best_row:
                stage = best_row[0]
                stage_scores = {
                    "L0": 0.2, "L1": 0.3, "L2": 0.4, "L3": 0.5,
                    "L4": 0.6, "L5": 0.7, "L6": 0.8, "L7": 0.9,
                    "P0": 1.0, "P1": 1.0, "P2": 1.0,
                    "LOST": 0.0, "HOLD": 0.1,
                }
                progress_pct = stage_scores.get(stage, 0.0)
            else:
                progress_pct = 0.0
            breakdown["deal_progress"] = round(progress_pct * HEALTH_SCORE_WEIGHTS["deal_progress"], 1)

            total_score = round(sum(breakdown.values()))
            status = (
                "healthy" if total_score >= HEALTH_SCORE_THRESHOLDS["healthy"]
                else "at_risk" if total_score >= HEALTH_SCORE_THRESHOLDS["at_risk"]
                else "critical"
            )

            return {
                "score": total_score,
                "status": status,
                "breakdown": breakdown,
            }


def compute_all_scores():
    """Compute health scores for all clients. Returns list of dicts with client_id + score + status."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT client_id FROM crm ORDER BY client_id")
            client_ids = [r[0] for r in cur.fetchall()]

    results = []
    for cid in client_ids:
        result = compute_health_score(cid)
        results.append({"client_id": cid, **result})
    return results
