"""CRM service — Client CRUD, normalized contact sync.

S15: reads/writes contacts via normalized tables only (JSONB dual-write retired).
S30: Refactored connection management to prevent nested connections.

Public API:
    create(client_id, ...) → None
    get_all() → list[dict]          # includes dm_name, champion_names via JOIN
    get_by_id(client_id) → dict     # includes decision_maker, champions from normalized
    update(client_id, ...) → None
    delete(client_id) → None
    find_or_create_client(company_name) -> str  # Returns client_id
Internal:
    _create(cur, client_id, ...)
    _sync_contacts_to_normalized(cur, client_id, dm, champions)
    _upsert_contact(cur, data) → contact_id
    _get_normalized_contacts(cur, client_id) → dict
"""
import re
from datetime import date
import streamlit as st
from database.connection import get_connection, read_sql_file


def create(client_id, company_name, industry=None, department=None, email=None,
           decision_maker=None, champions=None, contact_info=None, notes=None,
           data_year=None):
    """Public method to create a client. Manages its own connection."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            _create(cur, client_id, company_name, industry, department, email,
                    decision_maker, champions, contact_info, notes, data_year)


def find_or_create_client(company_name: str) -> str | None:
    """
    Finds a client by company name. If not found, creates a new one
    with a standard sequential ID (CLI-XXX).
    This function manages a single connection for the entire find-or-create transaction.
    Returns the client_id.
    """
    if not company_name or not company_name.strip():
        return None

    company_name = company_name.strip()

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Try to find an existing client
            cur.execute("SELECT client_id FROM crm WHERE company_name = %s", (company_name,))
            row = cur.fetchone()
            if row:
                return row[0]

            # If not found, create a new one with a sequential ID
            cur.execute("SELECT client_id FROM crm WHERE client_id LIKE 'CLI-%'")
            existing_ids = [r[0] for r in cur.fetchall()]

            max_id = 0
            for client_id in existing_ids:
                try:
                    num_part = int(client_id.split('-')[1])
                    if num_part > max_id:
                        max_id = num_part
                except (ValueError, IndexError):
                    continue

            new_id_num = max_id + 1
            new_client_id = f"CLI-{new_id_num:03d}"

            # Call the internal _create function with the current cursor
            _create(cur, client_id=new_client_id, company_name=company_name)
            
            return new_client_id


@st.cache_data
def get_all():
    """Get all clients with DM and champion names from normalized tables (LEFT JOIN)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            sql = read_sql_file("crm_get_all.sql")
            cur.execute(sql)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_by_id(client_id):
    """Get CRM record with contacts from normalized tables."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM crm WHERE client_id = %s", (client_id,))
            row = cur.fetchone()
            if row is None:
                return None
            cols = [d[0] for d in cur.description]
            result = dict(zip(cols, row))

            # Read from normalized tables (sole source of truth)
            contacts = _get_normalized_contacts(cur, client_id)
            if contacts is not None:
                result["decision_maker"] = contacts["decision_maker"]
                result["champions"] = contacts["champions"]

            return result


def update(client_id, company_name, industry, department, email=None,
           decision_maker=None, champions=None, contact_info=None, notes=None,
           data_year=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Update CRM row without JSONB fields
            cur.execute(
                """UPDATE crm
                   SET company_name = %s, industry = %s, department = %s,
                       email = %s, contact_info = %s, notes = %s, data_year = %s,
                       updated_at = NOW()
                   WHERE client_id = %s""",
                (company_name, industry, department, email,
                 contact_info, notes, data_year, client_id),
            )
            # Write contacts to normalized tables only
            _sync_contacts_to_normalized(cur, client_id, decision_maker, champions)


def delete(client_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            # account_contact rows cascade-deleted via FK
            cur.execute("DELETE FROM crm WHERE client_id = %s", (client_id,))


# ---------------------------------------------------------------------------
# Internal helpers — these operate on a provided cursor
# ---------------------------------------------------------------------------

def _create(cur, client_id, company_name, industry=None, department=None, email=None,
            decision_maker=None, champions=None, contact_info=None, notes=None,
            data_year=None):
    """Internal method to create a client using a provided cursor."""
    # Insert CRM row without JSONB fields
    cur.execute(
        """INSERT INTO crm
           (client_id, company_name, industry, department, email,
            contact_info, notes, data_year)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
           ON CONFLICT (client_id) DO NOTHING""",
        (client_id, company_name, industry, department, email,
         contact_info, notes, data_year or date.today().year),
    )
    # Write contacts to normalized tables only
    _sync_contacts_to_normalized(cur, client_id, decision_maker, champions)


def _sync_contacts_to_normalized(cur, client_id, decision_maker, champions):
    """Replace all normalized contacts for a client with the provided data."""
    # Remove existing links (contacts orphaned here will be cleaned up below)
    cur.execute("DELETE FROM account_contact WHERE client_id = %s", (client_id,))

    # Insert decision_maker
    if decision_maker and isinstance(decision_maker, dict) and decision_maker.get("name"):
        contact_id = _upsert_contact(cur, decision_maker)
        if contact_id:
            cur.execute("""
                INSERT INTO account_contact (client_id, contact_id, role, sort_order)
                VALUES (%s, %s, 'decision_maker', 0)
                ON CONFLICT (client_id, contact_id) DO UPDATE
                SET role = 'decision_maker', sort_order = 0
            """, (client_id, contact_id))

    # Insert champions
    if champions and isinstance(champions, list):
        for idx, ch in enumerate(champions):
            if isinstance(ch, dict) and ch.get("name"):
                contact_id = _upsert_contact(cur, ch)
                if contact_id:
                    cur.execute("""
                        INSERT INTO account_contact (client_id, contact_id, role, sort_order)
                        VALUES (%s, %s, 'champion', %s)
                        ON CONFLICT (client_id, contact_id) DO UPDATE
                        SET role = 'champion', sort_order = %s
                    """, (client_id, contact_id, idx, idx))

    # Clean up orphaned contacts (no links anywhere)
    cur.execute("""
        DELETE FROM contact
        WHERE contact_id NOT IN (SELECT contact_id FROM account_contact)
          AND contact_id NOT IN (SELECT contact_id FROM project_contact)
    """)


def _upsert_contact(cur, data):
    """Find or create a contact by name+email, return contact_id."""
    name = (data.get("name") or "").strip()
    if not name:
        return None

    email = (data.get("email") or "").strip() or None
    title = (data.get("title") or "").strip() or None
    phone = (data.get("phone") or "").strip() or None
    notes = (data.get("notes") or "").strip() or None

    # Try to find existing contact by name + email
    cur.execute("""
        SELECT contact_id FROM contact
        WHERE name = %s AND COALESCE(email, '') = COALESCE(%s, '')
    """, (name, email))
    existing = cur.fetchone()

    if existing:
        contact_id = existing[0]
        cur.execute("""
            UPDATE contact SET title = %s, phone = %s, notes = %s, updated_at = NOW()
            WHERE contact_id = %s
        """, (title, phone, notes, contact_id))
        return contact_id

    # Create new contact
    cur.execute("""
        INSERT INTO contact (name, title, email, phone, notes)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING contact_id
    """, (name, title, email, phone, notes))
    return cur.fetchone()[0]


def _get_normalized_contacts(cur, client_id):
    """Read contacts from normalized tables and assemble into dict format."""
    cur.execute("""
        SELECT c.name, c.title, c.email, c.phone, c.notes, ac.role, ac.sort_order
        FROM contact c
        JOIN account_contact ac ON c.contact_id = ac.contact_id
        WHERE ac.client_id = %s
        ORDER BY ac.role DESC, ac.sort_order
    """, (client_id,))

    rows = cur.fetchall()
    if not rows:
        return None

    cols = [d[0] for d in cur.description]
    contacts = [dict(zip(cols, row)) for row in rows]

    dm = None
    champs = []
    for c in contacts:
        entry = {
            "name": c["name"] or "",
            "title": c["title"] or "",
            "email": c["email"] or "",
            "phone": c["phone"] or "",
            "notes": c["notes"] or "",
        }
        if c["role"] == "decision_maker":
            dm = entry
        else:
            champs.append(entry)

    return {"decision_maker": dm, "champions": champs if champs else None}
