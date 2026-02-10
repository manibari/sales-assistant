"""S09 migration — create project_task table (idempotent)."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection

SQL = """
CREATE TABLE IF NOT EXISTS project_task (
    task_id         SERIAL PRIMARY KEY,
    project_id      INTEGER NOT NULL REFERENCES project_list(project_id)
                    ON DELETE CASCADE,
    task_name       TEXT NOT NULL,
    owner           TEXT,
    status          TEXT NOT NULL DEFAULT 'planned',
    start_date      DATE,
    end_date        DATE,
    estimated_hours NUMERIC NOT NULL DEFAULT 0,
    actual_hours    NUMERIC NOT NULL DEFAULT 0,
    sort_order      INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
"""


def migrate():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(SQL)
    print("S09 migration complete — project_task table ready.")


if __name__ == "__main__":
    migrate()
