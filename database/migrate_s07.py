"""S07 migration — add department, presale_owner, postsale_owner columns."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection


def migrate():
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Add department to crm
            cur.execute("ALTER TABLE crm ADD COLUMN IF NOT EXISTS department TEXT")

            # Add presale_owner, postsale_owner to project_list
            cur.execute("ALTER TABLE project_list ADD COLUMN IF NOT EXISTS presale_owner TEXT")
            cur.execute("ALTER TABLE project_list ADD COLUMN IF NOT EXISTS postsale_owner TEXT")

            # Check if old 'owner' column exists and migrate data
            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'project_list' AND column_name = 'owner'
            """)
            if cur.fetchone():
                cur.execute("UPDATE project_list SET presale_owner = owner WHERE presale_owner IS NULL")
                cur.execute("ALTER TABLE project_list DROP COLUMN owner")

            # Update default for status_code
            cur.execute("ALTER TABLE project_list ALTER COLUMN status_code SET DEFAULT 'L0'")

    print("S07 migration complete!")
    print("  - crm: added department column")
    print("  - project_list: added presale_owner, postsale_owner; removed owner")
    print("  - project_list: status_code default changed to 'L0'")


if __name__ == "__main__":
    migrate()
