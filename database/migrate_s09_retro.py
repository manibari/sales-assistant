"""S09 retro migration — add sales_owner column to project_list (idempotent)."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection

SQL = """
ALTER TABLE project_list ADD COLUMN IF NOT EXISTS sales_owner TEXT;
"""


def migrate():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(SQL)
    print("S09 retro migration complete — sales_owner column added.")


if __name__ == "__main__":
    migrate()
