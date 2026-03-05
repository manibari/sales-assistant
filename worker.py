"""
Asynchronous AI Task Queue Worker.

This script runs in a separate process, continuously checking the
`ai_task_queue` table for pending jobs and processing them.
"""
import logging
import sys
import os
import time
from datetime import date

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Add project root to path to allow imports from services
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from constants import ACTION_TYPES
from services import crm as crm_svc
from services import intelligent_log as il_svc
from services import project as project_svc
from services import task_queue as task_queue_svc
from services import work_log as work_log_svc

def process_single_task():
    """
    Fetches and processes a single pending task from the queue.
    Supports batch entries: AI may return multiple parsed entries for one task.
    """
    logger.info("Checking for new tasks...")
    task = task_queue_svc.get_next_pending()

    if not task:
        logger.debug("No pending tasks. Waiting...")
        return

    task_id = task["task_id"]
    raw_text = task["raw_text"]
    logger.info("Processing task #%d...", task_id)

    try:
        # 1. Parse text with AI (returns list[dict] or None)
        entries = il_svc.parse_log_entry(raw_text)
        if not entries:
            raise ValueError("AI parsing returned no entries.")

        logger.info("  AI returned %d entry/entries.", len(entries))

        results = []
        errors = []

        for i, entry in enumerate(entries):
            try:
                company_name = entry.get("company_name")
                if not company_name:
                    errors.append(f"Entry {i+1}: missing company_name")
                    continue

                logger.info("  [%d/%d] Processing: %s", i+1, len(entries), company_name)

                # 2. Find or create CRM entry
                client_id = crm_svc.find_or_create_client(company_name)
                if not client_id:
                    errors.append(f"Entry {i+1} ({company_name}): failed to find/create client")
                    continue

                # 3. Create work log
                work_log_svc.create(
                    client_id=client_id,
                    action_type=entry.get("action_type", ACTION_TYPES[0]),
                    log_date=date.today(),
                    content=entry.get("log_content", raw_text),
                    duration_hours=1.0,
                    source="ai"
                )

                # 4. Create project if implied
                project_name = entry.get("project_name")
                status_code = entry.get("project_status_code")
                if project_name and status_code:
                    project_id = project_svc.find_or_create_project(
                        client_id=client_id,
                        project_name=project_name,
                        status_code=status_code,
                        sales_owner=entry.get("sales_owner"),
                        presale_owner=entry.get("presale_owner"),
                        channel=entry.get("channel"),
                    )
                    if project_id:
                        logger.info("    Found/Created project #%s", project_id)

                results.append(entry)

            except Exception as e:
                errors.append(f"Entry {i+1} ({entry.get('company_name', '?')}): {e}")

        # 5. Determine final status
        if results:
            error_msg = "; ".join(errors) if errors else None
            task_queue_svc.update_task_status(
                task_id=task_id,
                status="completed",
                result_data=results,
                error_message=error_msg,
            )
            logger.info(
                "Task #%d completed: %d succeeded, %d failed.",
                task_id, len(results), len(errors),
            )
        else:
            task_queue_svc.update_task_status(
                task_id=task_id,
                status="failed",
                error_message="; ".join(errors) if errors else "All entries failed.",
            )
            logger.error("Task #%d failed: all entries failed.", task_id)

    except Exception as e:
        error_message = str(e)
        logger.error("Task #%d failed: %s", task_id, error_message)
        task_queue_svc.update_task_status(
            task_id=task_id,
            status="failed",
            error_message=error_message
        )

def main_loop():
    """
    Main worker loop to continuously process tasks.
    """
    logger.info("AI Worker started. Press Ctrl+C to exit.")
    while True:
        process_single_task()
        # Wait for 10 seconds before checking for new tasks
        time.sleep(10)

if __name__ == "__main__":
    main_loop()
