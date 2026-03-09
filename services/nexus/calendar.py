"""Nexus calendar service — meetings and reminders."""

from database.connection import get_connection, row_to_dict, rows_to_dicts


# --- Meetings ---

def create_meeting(
    deal_id: int,
    title: str,
    meeting_date: str,
    participants_json: str | None = None,
    location: str | None = None,
    notes: str | None = None,
) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO nx_meeting (deal_id, title, meeting_date, participants_json, location, notes)
                   VALUES (%s, %s, %s, %s, %s, %s)
                   RETURNING *""",
                (deal_id, title, meeting_date, participants_json, location, notes),
            )
            return row_to_dict(cur)


def get_meeting(meeting_id: int) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT m.*, d.name AS deal_name, c.name AS client_name
                   FROM nx_meeting m
                   JOIN nx_deal d ON m.deal_id = d.id
                   JOIN nx_client c ON d.client_id = c.id
                   WHERE m.id = %s""",
                (meeting_id,),
            )
            return row_to_dict(cur)


def get_meetings_by_date(date_str: str) -> list[dict]:
    """Get meetings for a given date (YYYY-MM-DD)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT m.*, d.name AS deal_name, c.name AS client_name
                   FROM nx_meeting m
                   JOIN nx_deal d ON m.deal_id = d.id
                   JOIN nx_client c ON d.client_id = c.id
                   WHERE date(m.meeting_date) = %s
                   ORDER BY m.meeting_date ASC""",
                (date_str,),
            )
            return rows_to_dicts(cur)


def get_meetings_by_month(year: int, month: int) -> list[dict]:
    """Get all meetings in a month (for calendar dot indicators)."""
    month_str = f"{year}-{month:02d}"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT m.id, m.deal_id, m.title, m.meeting_date, m.status,
                          d.name AS deal_name
                   FROM nx_meeting m
                   JOIN nx_deal d ON m.deal_id = d.id
                   WHERE strftime('%%Y-%%m', m.meeting_date) = %s
                   ORDER BY m.meeting_date ASC""",
                (month_str,),
            )
            return rows_to_dicts(cur)


def get_meetings_by_deal(deal_id: int) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT * FROM nx_meeting WHERE deal_id = %s ORDER BY meeting_date DESC""",
                (deal_id,),
            )
            return rows_to_dicts(cur)


def update_meeting(meeting_id: int, **fields) -> dict | None:
    if not fields:
        return get_meeting(meeting_id)
    allowed = {"title", "meeting_date", "participants_json", "location", "notes", "status"}
    filtered = {k: v for k, v in fields.items() if k in allowed}
    if not filtered:
        return get_meeting(meeting_id)
    set_clause = ", ".join(f"{k} = %s" for k in filtered)
    values = list(filtered.values()) + [meeting_id]
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE nx_meeting SET {set_clause}, updated_at = datetime('now') WHERE id = %s RETURNING *",
                values,
            )
            return row_to_dict(cur)


def complete_meeting(meeting_id: int) -> dict | None:
    return update_meeting(meeting_id, status="completed")


def delete_meeting(meeting_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM nx_meeting WHERE id = %s", (meeting_id,))
            return cur._cur.rowcount > 0


# --- Reminders ---

def create_reminder(
    due_date: str,
    content: str,
    reminder_type: str = "custom",
    deal_id: int | None = None,
) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO nx_reminder (deal_id, reminder_type, due_date, content)
                   VALUES (%s, %s, %s, %s)
                   RETURNING *""",
                (deal_id, reminder_type, due_date, content),
            )
            return row_to_dict(cur)


def get_reminders_by_date(date_str: str) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT r.*, d.name AS deal_name
                   FROM nx_reminder r
                   LEFT JOIN nx_deal d ON r.deal_id = d.id
                   WHERE date(r.due_date) = %s AND r.resolved = 0
                   ORDER BY r.due_date ASC""",
                (date_str,),
            )
            return rows_to_dicts(cur)


def get_reminders_by_month(year: int, month: int) -> list[dict]:
    month_str = f"{year}-{month:02d}"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT r.id, r.deal_id, r.reminder_type, r.due_date, r.content, r.resolved,
                          d.name AS deal_name
                   FROM nx_reminder r
                   LEFT JOIN nx_deal d ON r.deal_id = d.id
                   WHERE strftime('%%Y-%%m', r.due_date) = %s
                   ORDER BY r.due_date ASC""",
                (month_str,),
            )
            return rows_to_dicts(cur)


def resolve_reminder(reminder_id: int) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE nx_reminder SET resolved = 1, resolved_at = datetime('now')
                   WHERE id = %s RETURNING *""",
                (reminder_id,),
            )
            return row_to_dict(cur)


def get_pending_reminders() -> list[dict]:
    """Get all unresolved reminders up to today."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT r.*, d.name AS deal_name
                   FROM nx_reminder r
                   LEFT JOIN nx_deal d ON r.deal_id = d.id
                   WHERE r.resolved = 0 AND date(r.due_date) <= date('now')
                   ORDER BY r.due_date ASC"""
            )
            return rows_to_dicts(cur)
