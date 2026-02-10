"""S12 migration: add due_date + is_next_action to project_task."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection


def migrate():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                ALTER TABLE project_task
                ADD COLUMN IF NOT EXISTS due_date DATE
            """)
            cur.execute("""
                ALTER TABLE project_task
                ADD COLUMN IF NOT EXISTS is_next_action BOOLEAN DEFAULT FALSE
            """)
            print("S12 migration complete:")
            print("  Added project_task.due_date (DATE)")
            print("  Added project_task.is_next_action (BOOLEAN DEFAULT FALSE)")


if __name__ == "__main__":
    migrate()
