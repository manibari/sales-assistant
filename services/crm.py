"""CRUD operations for crm table. Uses psycopg2.extras.Json for JSONB fields."""

from psycopg2.extras import Json

from database.connection import get_connection


def create(client_id, company_name, industry=None, email=None,
           decision_maker=None, champion=None, contact_info=None, notes=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO crm
                   (client_id, company_name, industry, email, decision_maker, champion, contact_info, notes)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (client_id, company_name, industry, email,
                 Json(decision_maker) if decision_maker else None,
                 Json(champion) if champion else None,
                 contact_info, notes),
            )


def get_all():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM crm ORDER BY client_id")
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_by_id(client_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM crm WHERE client_id = %s", (client_id,))
            row = cur.fetchone()
            if row is None:
                return None
            cols = [d[0] for d in cur.description]
            return dict(zip(cols, row))


def update(client_id, company_name, industry, email,
           decision_maker, champion, contact_info, notes):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE crm
                   SET company_name = %s, industry = %s, email = %s,
                       decision_maker = %s, champion = %s,
                       contact_info = %s, notes = %s, updated_at = NOW()
                   WHERE client_id = %s""",
                (company_name, industry, email,
                 Json(decision_maker) if decision_maker else None,
                 Json(champion) if champion else None,
                 contact_info, notes, client_id),
            )


def delete(client_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM crm WHERE client_id = %s", (client_id,))
