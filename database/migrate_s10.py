"""Idempotent migration: JSONB contacts → normalized contact + account_contact tables."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection


def migrate():
    with get_connection() as conn:
        with conn.cursor() as cur:
            # 1. Create tables (idempotent)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS contact (
                    contact_id   SERIAL PRIMARY KEY,
                    name         TEXT NOT NULL,
                    title        TEXT,
                    email        TEXT,
                    phone        TEXT,
                    notes        TEXT,
                    created_at   TIMESTAMPTZ DEFAULT NOW(),
                    updated_at   TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS account_contact (
                    client_id    TEXT NOT NULL REFERENCES crm(client_id) ON DELETE CASCADE,
                    contact_id   INTEGER NOT NULL REFERENCES contact(contact_id) ON DELETE CASCADE,
                    role         TEXT NOT NULL DEFAULT 'champion',
                    sort_order   INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (client_id, contact_id)
                )
            """)

            # 2. Read all CRM records
            cur.execute("SELECT client_id, decision_maker, champions FROM crm")
            rows = cur.fetchall()

            stats = {"dm_migrated": 0, "champ_migrated": 0, "skipped": 0}

            for client_id, dm, champions in rows:
                # 3. Migrate decision_maker
                if dm and isinstance(dm, dict) and dm.get("name"):
                    contact_id = _upsert_contact(cur, client_id, dm, "decision_maker")
                    if contact_id:
                        stats["dm_migrated"] += 1
                    else:
                        stats["skipped"] += 1

                # 4. Migrate champions
                if champions:
                    champ_list = champions if isinstance(champions, list) else [champions]
                    for idx, ch in enumerate(champ_list):
                        if isinstance(ch, dict) and ch.get("name"):
                            contact_id = _upsert_contact(
                                cur, client_id, ch, "champion", sort_order=idx
                            )
                            if contact_id:
                                stats["champ_migrated"] += 1
                            else:
                                stats["skipped"] += 1

            print(f"Migration complete:")
            print(f"  Decision makers migrated: {stats['dm_migrated']}")
            print(f"  Champions migrated: {stats['champ_migrated']}")
            print(f"  Skipped (duplicates): {stats['skipped']}")

            # Print totals
            cur.execute("SELECT COUNT(*) FROM contact")
            total_contacts = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM account_contact")
            total_links = cur.fetchone()[0]
            print(f"  Total contacts: {total_contacts}")
            print(f"  Total account_contact links: {total_links}")


def _upsert_contact(cur, client_id, data, role, sort_order=0):
    """Insert contact if not duplicate (by name + email + client_id), return contact_id or None."""
    name = data.get("name", "").strip()
    email = data.get("email", "").strip() or None
    if not name:
        return None

    # Check for existing duplicate: same name, email, and already linked to this client
    cur.execute("""
        SELECT c.contact_id FROM contact c
        JOIN account_contact ac ON c.contact_id = ac.contact_id
        WHERE c.name = %s AND ac.client_id = %s
          AND COALESCE(c.email, '') = COALESCE(%s, '')
    """, (name, client_id, email))
    existing = cur.fetchone()

    if existing:
        return None  # duplicate

    # Insert new contact
    cur.execute("""
        INSERT INTO contact (name, title, email, phone, notes)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING contact_id
    """, (
        name,
        data.get("title", "").strip() or None,
        email,
        data.get("phone", "").strip() or None,
        data.get("notes", "").strip() or None,
    ))
    contact_id = cur.fetchone()[0]

    # Link to client
    cur.execute("""
        INSERT INTO account_contact (client_id, contact_id, role, sort_order)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (client_id, contact_id) DO NOTHING
    """, (client_id, contact_id, role, sort_order))

    return contact_id


if __name__ == "__main__":
    migrate()
