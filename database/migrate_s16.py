"""S16 Migration — Contact deduplication + UNIQUE INDEX.

1. Detects duplicate contacts by (name, COALESCE(email, ''))
2. Merges duplicates: keeps smallest contact_id, re-points FKs
3. Adds UNIQUE INDEX to prevent future duplicates
"""

from database.connection import get_connection


def migrate():
    with get_connection() as conn:
        with conn.cursor() as cur:
            # 1. Find duplicate groups
            cur.execute("""
                SELECT name, COALESCE(email, '') AS email_key,
                       ARRAY_AGG(contact_id ORDER BY contact_id) AS ids
                FROM contact
                GROUP BY name, COALESCE(email, '')
                HAVING COUNT(*) > 1
            """)
            dup_groups = cur.fetchall()

            total_merged = 0
            for name, email_key, ids in dup_groups:
                keep_id = ids[0]  # smallest contact_id
                remove_ids = ids[1:]

                for old_id in remove_ids:
                    # Re-point account_contact FKs
                    cur.execute("""
                        UPDATE account_contact SET contact_id = %s
                        WHERE contact_id = %s
                        AND NOT EXISTS (
                            SELECT 1 FROM account_contact
                            WHERE client_id = account_contact.client_id AND contact_id = %s
                        )
                    """, (keep_id, old_id, keep_id))
                    # Delete conflicting account_contact rows
                    cur.execute("DELETE FROM account_contact WHERE contact_id = %s", (old_id,))

                    # Re-point project_contact FKs
                    cur.execute("""
                        UPDATE project_contact SET contact_id = %s
                        WHERE contact_id = %s
                        AND NOT EXISTS (
                            SELECT 1 FROM project_contact
                            WHERE project_id = project_contact.project_id AND contact_id = %s
                        )
                    """, (keep_id, old_id, keep_id))
                    # Delete conflicting project_contact rows
                    cur.execute("DELETE FROM project_contact WHERE contact_id = %s", (old_id,))

                    # Delete the duplicate contact
                    cur.execute("DELETE FROM contact WHERE contact_id = %s", (old_id,))
                    total_merged += 1

                print(f"  Merged {name} ({email_key or 'no email'}): kept #{keep_id}, removed {remove_ids}")

            print(f"\n[S16] Deduplicated {total_merged} contact(s) across {len(dup_groups)} group(s).")

            # 2. Create UNIQUE INDEX
            cur.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS contact_name_email_unique
                ON contact (name, COALESCE(email, ''))
            """)
            print("[S16] UNIQUE INDEX contact_name_email_unique created.")


if __name__ == "__main__":
    migrate()
    print("S16 migration complete.")
