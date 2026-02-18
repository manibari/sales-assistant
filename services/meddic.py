"""MEDDIC service — CRUD for the project_meddic table."""

from database.connection import get_connection, row_to_dict

def get_by_project(project_id: int) -> dict | None:
    """
    Retrieves the MEDDIC record for a given project_id.

    Returns:
        A dictionary representing the MEDDIC record, or None if not found.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM project_meddic WHERE project_id = %s", (project_id,))
            return row_to_dict(cur)

def save_or_update(
    project_id: int,
    metrics: str,
    economic_buyer: str,
    decision_criteria: str,
    decision_process: str,
    identify_pain: str,
    champion: str
) -> None:
    """
    Saves or updates the MEDDIC record for a project using INSERT ON CONFLICT.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO project_meddic (
                    project_id, metrics, economic_buyer, decision_criteria,
                    decision_process, identify_pain, champion, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (project_id) DO UPDATE SET
                    metrics = EXCLUDED.metrics,
                    economic_buyer = EXCLUDED.economic_buyer,
                    decision_criteria = EXCLUDED.decision_criteria,
                    decision_process = EXCLUDED.decision_process,
                    identify_pain = EXCLUDED.identify_pain,
                    champion = EXCLUDED.champion,
                    updated_at = NOW()
                """,
                (
                    project_id, metrics, economic_buyer, decision_criteria,
                    decision_process, identify_pain, champion
                ),
            )
