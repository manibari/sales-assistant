"""Idempotent migration: champion → champions (array), decision_maker structure update."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection


def migrate():
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Check if column has already been renamed
            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'crm' AND column_name = 'champion'
            """)
            needs_rename = cur.fetchone() is not None

            # Always add data_year if missing
            cur.execute("""
                ALTER TABLE crm ADD COLUMN IF NOT EXISTS data_year INTEGER
            """)

            if needs_rename:
                # 1) Rename column
                cur.execute("ALTER TABLE crm RENAME COLUMN champion TO champions")

                # 2) Wrap existing single champion object into array
                cur.execute("""
                    UPDATE crm
                    SET champions = jsonb_build_array(champions)
                    WHERE champions IS NOT NULL
                      AND jsonb_typeof(champions) = 'object'
                """)

                # 3) Update decision_maker: add email/phone/notes, remove style
                cur.execute("""
                    UPDATE crm
                    SET decision_maker = (decision_maker - 'style')
                        || jsonb_build_object(
                            'email', '',
                            'phone', COALESCE(contact_info, ''),
                            'notes', COALESCE(decision_maker->>'style', '')
                        )
                    WHERE decision_maker IS NOT NULL
                """)

                print("Migration complete: champion → champions, decision_maker updated.")
            else:
                print("Column rename already applied — skipping.")

            print("data_year column ensured.")


if __name__ == "__main__":
    migrate()
