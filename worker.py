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
        # 1. Parse text with AI
        parsed_data = il_svc.parse_log_entry(raw_text)
        if not parsed_data or not parsed_data.get("company_name"):
            raise ValueError("AI parsing failed to return a valid company name.")

        company_name = parsed_data["company_name"]
        logger.info("  AI parsed company: %s", company_name)

        # 2. Find or create CRM entry
        client_id = crm_svc.find_or_create_client(company_name)
        if not client_id:
            raise ValueError(f"Failed to find or create client ID for '{company_name}'.")
        logger.info("  Found/Created client: %s", client_id)

        # 3. Create work log
        work_log_svc.create(
            client_id=client_id,
            action_type=parsed_data.get("action_type", ACTION_TYPES[0]),
            log_date=date.today(),
            content=parsed_data.get("log_content", raw_text),
            duration_hours=1.0,
            source="ai"
        )
        logger.info("  Created work log entry.")

        # 4. Create project if implied
        project_name = parsed_data.get("project_name")
        status_code = parsed_data.get("project_status_code")
        if project_name and status_code:
            project_id = project_svc.find_or_create_project(
                client_id=client_id,
                project_name=project_name,
                status_code=status_code
            )
            if project_id:
                logger.info("  Found/Created project: %s", project_id)

        # 5. Mark task as completed
        task_queue_svc.update_task_status(
            task_id=task_id,
            status="completed",
            result_data=parsed_data
        )
        logger.info("Task #%d completed successfully.", task_id)

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
