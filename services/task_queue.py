"""
Service for managing the ai_task_queue table.

This service encapsulates all database interactions for the asynchronous
AI processing queue.
"""

from database.connection import get_connection, row_to_dict, rows_to_dicts

def create_task(raw_text: str) -> int:
    """
    Creates a new task in the AI queue with 'pending' status.

    Args:
        raw_text: The user's unstructured text input.

    Returns:
        The ID of the newly created task.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO ai_task_queue (raw_text) VALUES (%s) RETURNING task_id",
                (raw_text,),
            )
            task_id = cur.fetchone()[0]
            return task_id

def get_next_pending() -> dict | None:
    """
    Atomically fetches the oldest pending task and sets its status to 'processing'.
    This prevents other workers from picking up the same task.

    Returns:
        A dictionary representing the task, or None if no pending tasks exist.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            # FOR UPDATE SKIP LOCKED ensures that we grab a task that isn't already
            # being processed by another worker instance.
            cur.execute(
                """
                UPDATE ai_task_queue
                SET status = 'processing', processed_at = NOW()
                WHERE task_id = (
                    SELECT task_id
                    FROM ai_task_queue
                    WHERE status = 'pending'
                    ORDER BY created_at
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                )
                RETURNING *
                """
            )
            return row_to_dict(cur)

def get_recent_tasks(limit: int = 20) -> list[dict]:
    """
    Retrieves the most recent tasks from the queue.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM ai_task_queue ORDER BY created_at DESC LIMIT %s",
                (limit,)
            )
            return rows_to_dicts(cur)


def update_task_status(
    task_id: int,
    status: str,
    result_data: dict = None,
    error_message: str = None
):
    """
    Updates the status and result of a task in the queue.

    Args:
        task_id: The ID of the task to update.
        status: The new status ('completed' or 'failed').
        result_data: The JSON-serializable result from the AI service.
        error_message: A description of the error if the task failed.
    """
    from psycopg2.extras import Json

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE ai_task_queue
                SET status = %s,
                    result_data = %s,
                    error_message = %s,
                    processed_at = NOW()
                WHERE task_id = %s
                """,
                (status, Json(result_data) if result_data else None, error_message, task_id),
            )
