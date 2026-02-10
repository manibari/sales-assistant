"""S11 migration: stage_probability + project_contact tables."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection


# Default probabilities per stage
_SEED_DATA = [
    ("L0", 0.05, 1),
    ("L1", 0.10, 2),
    ("L2", 0.20, 3),
    ("L3", 0.30, 4),
    ("L4", 0.50, 5),
    ("L5", 0.60, 6),
    ("L6", 0.75, 7),
    ("L7", 1.00, 8),
    ("P0", 1.00, 9),
    ("P1", 1.00, 10),
    ("P2", 1.00, 11),
    ("LOST", 0.00, 12),
    ("HOLD", 0.05, 13),
]


def migrate():
    with get_connection() as conn:
        with conn.cursor() as cur:
            # 1. Create stage_probability table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS stage_probability (
                    status_code  TEXT PRIMARY KEY,
                    probability  NUMERIC NOT NULL DEFAULT 0.5
                        CHECK (probability >= 0 AND probability <= 1),
                    sort_order   INTEGER NOT NULL DEFAULT 0
                )
            """)

            # 2. Create project_contact table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS project_contact (
                    project_id   INTEGER NOT NULL REFERENCES project_list(project_id) ON DELETE CASCADE,
                    contact_id   INTEGER NOT NULL REFERENCES contact(contact_id) ON DELETE CASCADE,
                    role         TEXT NOT NULL DEFAULT 'participant',
                    PRIMARY KEY (project_id, contact_id)
                )
            """)

            # 3. Seed stage_probability (idempotent)
            for status_code, probability, sort_order in _SEED_DATA:
                cur.execute("""
                    INSERT INTO stage_probability (status_code, probability, sort_order)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (status_code) DO NOTHING
                """, (status_code, probability, sort_order))

            # Print results
            cur.execute("SELECT COUNT(*) FROM stage_probability")
            total = cur.fetchone()[0]
            print(f"S11 migration complete:")
            print(f"  stage_probability rows: {total}")

            cur.execute("SELECT status_code, probability FROM stage_probability ORDER BY sort_order")
            for code, prob in cur.fetchall():
                print(f"    {code}: {prob}")


if __name__ == "__main__":
    migrate()
