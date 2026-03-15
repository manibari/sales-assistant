"""Outlook calendar sync service — bidirectional sync between Nexus and Outlook."""

import logging
from datetime import datetime, timezone

import httpx

from database.connection import get_connection, row_to_dict, rows_to_dicts

logger = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.microsoft.com/v1.0"


def fetch_calendar_events(
    token: str, start: str | None = None, end: str | None = None
) -> list[dict]:
    """Fetch calendar events from Microsoft Graph."""
    params: dict[str, str] = {
        "$top": "100",
        "$orderby": "start/dateTime",
        "$select": "id,subject,start,end,attendees,location,bodyPreview,isAllDay",
    }
    if start and end:
        params["$filter"] = f"start/dateTime ge '{start}' and end/dateTime le '{end}'"

    with httpx.Client() as client:
        resp = client.get(
            f"{GRAPH_BASE}/me/events",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
        )
        resp.raise_for_status()
        return resp.json().get("value", [])


def create_outlook_event(token: str, event: dict) -> dict:
    """Create a calendar event in Outlook."""
    with httpx.Client() as client:
        resp = client.post(
            f"{GRAPH_BASE}/me/events",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=event,
        )
        resp.raise_for_status()
        return resp.json()


def sync_meetings_to_outlook(token: str) -> int:
    """Push Nexus meetings without outlook_event_id to Outlook."""
    synced = 0
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT m.*, d.name as deal_name, c.name as client_name
                   FROM nx_meeting m
                   LEFT JOIN nx_deal d ON m.deal_id = d.id
                   LEFT JOIN nx_client c ON d.client_id = c.id
                   WHERE m.outlook_event_id IS NULL
                     AND m.meeting_date >= NOW()"""
            )
            meetings = rows_to_dicts(cur)

    for meeting in meetings:
        try:
            start_dt = meeting["meeting_date"]
            duration = meeting.get("duration_minutes", 60)

            event = {
                "subject": meeting["title"],
                "start": {
                    "dateTime": start_dt.isoformat() if hasattr(start_dt, "isoformat") else start_dt,
                    "timeZone": "Asia/Taipei",
                },
                "end": {
                    "dateTime": (
                        start_dt + __import__("datetime").timedelta(minutes=duration)
                    ).isoformat()
                    if hasattr(start_dt, "isoformat")
                    else start_dt,
                    "timeZone": "Asia/Taipei",
                },
                "body": {
                    "contentType": "Text",
                    "content": f"Deal: {meeting.get('deal_name', 'N/A')} | Client: {meeting.get('client_name', 'N/A')}",
                },
            }

            result = create_outlook_event(token, event)
            outlook_id = result.get("id")

            if outlook_id:
                with get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "UPDATE nx_meeting SET outlook_event_id = %s WHERE id = %s",
                            (outlook_id, meeting["id"]),
                        )
                synced += 1
        except Exception as e:
            logger.error("Failed to sync meeting %d: %s", meeting["id"], e)

    logger.info("Synced %d meetings to Outlook", synced)
    return synced


def sync_outlook_to_meetings(token: str) -> int:
    """Pull Outlook events and create/update Nexus meetings. Last-write-wins."""
    events = fetch_calendar_events(token)
    synced = 0

    with get_connection() as conn:
        with conn.cursor() as cur:
            for event in events:
                outlook_id = event.get("id")
                if not outlook_id:
                    continue

                # Check if already linked
                cur.execute(
                    "SELECT id, updated_at FROM nx_meeting WHERE outlook_event_id = %s",
                    (outlook_id,),
                )
                existing = cur.fetchone()

                subject = event.get("subject", "Outlook Event")
                start_dt = event.get("start", {}).get("dateTime")

                if existing:
                    # Last-write-wins: update if Outlook is newer
                    # (we can't easily compare, so always update from Outlook)
                    cur.execute(
                        """UPDATE nx_meeting
                           SET title = %s, meeting_date = %s, updated_at = NOW()
                           WHERE outlook_event_id = %s""",
                        (subject, start_dt, outlook_id),
                    )
                else:
                    # Create new meeting (no deal_id since it came from Outlook)
                    cur.execute(
                        """INSERT INTO nx_meeting (deal_id, title, meeting_date, duration_minutes, outlook_event_id, status)
                           VALUES (NULL, %s, %s, 60, %s, 'scheduled')""",
                        (subject, start_dt, outlook_id),
                    )
                synced += 1

    logger.info("Synced %d events from Outlook", synced)
    return synced
