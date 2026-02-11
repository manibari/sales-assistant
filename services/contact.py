"""Contact service — CRUD for contact + account_contact tables.

Uses ON CONFLICT upsert on UNIQUE INDEX (name, COALESCE(email, '')) since S16.

Public API:
    create(name, ...) → contact_id          # upsert by name+email
    get_by_id(contact_id) → dict | None
    get_by_client(client_id) → list[dict]   # with role, sort_order
    update(contact_id, ...) → None
    delete(contact_id) → None
    link_to_client(client_id, contact_id, role, sort_order) → None
    unlink_from_client(client_id, contact_id) → None
"""

from database.connection import get_connection


def create(name, title=None, email=None, phone=None, notes=None):
    """Create or upsert a contact by (name, email). Returns contact_id."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO contact (name, title, email, phone, notes)
                   VALUES (%s, %s, %s, %s, %s)
                   ON CONFLICT (name, COALESCE(email, ''))
                   DO UPDATE SET title = EXCLUDED.title, phone = EXCLUDED.phone,
                                 notes = EXCLUDED.notes, updated_at = NOW()
                   RETURNING contact_id""",
                (name, title, email, phone, notes),
            )
            return cur.fetchone()[0]


def get_by_id(contact_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM contact WHERE contact_id = %s", (contact_id,))
            row = cur.fetchone()
            if row is None:
                return None
            cols = [d[0] for d in cur.description]
            return dict(zip(cols, row))


def get_by_client(client_id):
    """Get all contacts linked to a client, with role and sort_order."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT c.*, ac.role, ac.sort_order
                   FROM contact c
                   JOIN account_contact ac ON c.contact_id = ac.contact_id
                   WHERE ac.client_id = %s
                   ORDER BY ac.role DESC, ac.sort_order""",
                (client_id,),
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def update(contact_id, name, title=None, email=None, phone=None, notes=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE contact
                   SET name = %s, title = %s, email = %s, phone = %s,
                       notes = %s, updated_at = NOW()
                   WHERE contact_id = %s""",
                (name, title, email, phone, notes, contact_id),
            )


def delete(contact_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM contact WHERE contact_id = %s", (contact_id,))


def link_to_client(client_id, contact_id, role="champion", sort_order=0):
    """Link a contact to a client with a role."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO account_contact (client_id, contact_id, role, sort_order)
                   VALUES (%s, %s, %s, %s)
                   ON CONFLICT (client_id, contact_id) DO UPDATE
                   SET role = EXCLUDED.role, sort_order = EXCLUDED.sort_order""",
                (client_id, contact_id, role, sort_order),
            )


def unlink_from_client(client_id, contact_id):
    """Remove a contact-client link."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM account_contact WHERE client_id = %s AND contact_id = %s",
                (client_id, contact_id),
            )
