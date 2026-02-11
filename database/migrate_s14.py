"""S14 Migration — Client-level activity records.

Alters work_log to support activities not tied to a project:
  - project_id becomes nullable
  - new client_id FK to crm(client_id)
  - CHECK constraint: at least one of project_id or client_id must be set
"""

from database.connection import get_connection


def migrate():
    with get_connection() as conn:
        with conn.cursor() as cur:
            # 1. Add client_id column with FK reference
            cur.execute("""
                ALTER TABLE work_log
                ADD COLUMN IF NOT EXISTS client_id TEXT REFERENCES crm(client_id)
            """)

            # 2. Make project_id nullable
            cur.execute("""
                ALTER TABLE work_log
                ALTER COLUMN project_id DROP NOT NULL
            """)

            # 3. Add CHECK constraint ensuring at least one scope is set
            cur.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint
                        WHERE conname = 'work_log_scope_check'
                    ) THEN
                        ALTER TABLE work_log
                        ADD CONSTRAINT work_log_scope_check
                        CHECK (project_id IS NOT NULL OR client_id IS NOT NULL);
                    END IF;
                END
                $$
            """)

            print("[S14] work_log: project_id nullable, client_id FK added, scope CHECK added.")


if __name__ == "__main__":
    migrate()
    print("S14 migration complete.")
