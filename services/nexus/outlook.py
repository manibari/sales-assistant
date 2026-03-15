"""Outlook email service — fetch, send, sync via Microsoft Graph API."""

import logging

import httpx

from database.connection import get_connection, row_to_dict, rows_to_dicts

logger = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.microsoft.com/v1.0"


def fetch_inbox(token: str, top: int = 20, skip: int = 0) -> list[dict]:
    """Fetch inbox messages from Microsoft Graph."""
    with httpx.Client() as client:
        resp = client.get(
            f"{GRAPH_BASE}/me/messages",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "$top": top,
                "$skip": skip,
                "$orderby": "receivedDateTime desc",
                "$select": "id,subject,from,toRecipients,ccRecipients,bodyPreview,receivedDateTime,isRead,importance,hasAttachments,conversationId",
            },
        )
        resp.raise_for_status()
        return resp.json().get("value", [])


def get_email(token: str, message_id: str) -> dict:
    """Get a single email by ID."""
    with httpx.Client() as client:
        resp = client.get(
            f"{GRAPH_BASE}/me/messages/{message_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        return resp.json()


def send_email(token: str, to: list[str], subject: str, body: str) -> dict:
    """Send an email via Microsoft Graph."""
    message = {
        "message": {
            "subject": subject,
            "body": {"contentType": "HTML", "content": body},
            "toRecipients": [
                {"emailAddress": {"address": addr}} for addr in to
            ],
        }
    }
    with httpx.Client() as client:
        resp = client.post(
            f"{GRAPH_BASE}/me/sendMail",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=message,
        )
        resp.raise_for_status()
        return {"status": "sent"}


def reply_email(token: str, message_id: str, body: str) -> dict:
    """Reply to an email."""
    with httpx.Client() as client:
        resp = client.post(
            f"{GRAPH_BASE}/me/messages/{message_id}/reply",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={"comment": body},
        )
        resp.raise_for_status()
        return {"status": "replied"}


def sync_emails_to_db(token: str, max_pages: int = 3) -> int:
    """Sync recent emails from Graph to nx_email_thread. Returns count of new emails."""
    synced = 0
    skip = 0
    top = 50

    for _ in range(max_pages):
        messages = fetch_inbox(token, top=top, skip=skip)
        if not messages:
            break

        with get_connection() as conn:
            with conn.cursor() as cur:
                for msg in messages:
                    from_addr = msg.get("from", {}).get("emailAddress", {}).get("address", "")
                    to_addrs = ", ".join(
                        r.get("emailAddress", {}).get("address", "")
                        for r in msg.get("toRecipients", [])
                    )
                    cc_addrs = ", ".join(
                        r.get("emailAddress", {}).get("address", "")
                        for r in msg.get("ccRecipients", [])
                    )

                    cur.execute(
                        """INSERT INTO nx_email_thread
                           (message_id, conversation_id, subject, from_addr, to_addrs, cc_addrs,
                            body_preview, direction, received_at, is_read, importance, has_attachments, raw_json)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                           ON CONFLICT (message_id) DO NOTHING""",
                        (
                            msg["id"],
                            msg.get("conversationId"),
                            msg.get("subject"),
                            from_addr,
                            to_addrs,
                            cc_addrs,
                            msg.get("bodyPreview"),
                            "inbound",  # all fetched are inbound
                            msg.get("receivedDateTime"),
                            msg.get("isRead", False),
                            msg.get("importance", "normal"),
                            msg.get("hasAttachments", False),
                            __import__("json").dumps(msg),
                        ),
                    )
                    if cur.rowcount > 0:
                        synced += 1

        skip += top

    # Auto-associate after sync
    auto_associate_emails()

    logger.info("Synced %d new emails", synced)
    return synced


def auto_associate_emails() -> int:
    """Associate unlinked emails with contacts/clients by matching email addresses."""
    associated = 0
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Match from_addr or to_addrs against nx_contact.email
            cur.execute(
                """UPDATE nx_email_thread e
                   SET contact_id = c.id,
                       client_id = c.org_id
                   FROM nx_contact c
                   WHERE e.contact_id IS NULL
                     AND c.email IS NOT NULL
                     AND c.org_type = 'client'
                     AND (e.from_addr = c.email OR e.to_addrs LIKE '%%' || c.email || '%%')"""
            )
            associated = cur.rowcount
    logger.info("Auto-associated %d emails with contacts", associated)
    return associated


# --- DB queries ---


def get_emails(
    client_id: int | None = None,
    deal_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    """Get emails with optional filters."""
    conditions = []
    params: list = []

    if client_id is not None:
        conditions.append("client_id = %s")
        params.append(client_id)
    if deal_id is not None:
        conditions.append("deal_id = %s")
        params.append(deal_id)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""SELECT id, message_id, conversation_id, subject, from_addr, to_addrs,
                           cc_addrs, body_preview, direction, received_at, client_id, deal_id,
                           contact_id, is_read, importance, has_attachments, synced_at
                    FROM nx_email_thread {where}
                    ORDER BY received_at DESC
                    LIMIT %s OFFSET %s""",
                params + [limit, offset],
            )
            return rows_to_dicts(cur)


def get_email_by_id(email_id: int) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM nx_email_thread WHERE id = %s", (email_id,))
            return row_to_dict(cur)
