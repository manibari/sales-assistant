"""Outlook contacts sync service — bidirectional sync with nx_contact."""

import logging

import httpx

from database.connection import get_connection, row_to_dict, rows_to_dicts

logger = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.microsoft.com/v1.0"


def fetch_outlook_contacts(token: str, top: int = 200) -> list[dict]:
    """Fetch contacts from Microsoft Graph People API."""
    with httpx.Client() as client:
        resp = client.get(
            f"{GRAPH_BASE}/me/contacts",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "$top": top,
                "$select": "id,displayName,emailAddresses,businessPhones,jobTitle,companyName",
            },
        )
        resp.raise_for_status()
        return resp.json().get("value", [])


def sync_contacts_bidirectional(token: str) -> dict:
    """Bidirectional sync using email as match key.

    Returns:
        {"pushed": int, "pulled": int, "matched": int}
    """
    outlook_contacts = fetch_outlook_contacts(token)
    pushed = 0
    pulled = 0
    matched = 0

    # Build lookup by email from Outlook
    outlook_by_email: dict[str, dict] = {}
    for oc in outlook_contacts:
        emails = oc.get("emailAddresses", [])
        for em in emails:
            addr = em.get("address", "").lower().strip()
            if addr:
                outlook_by_email[addr] = oc

    # Get all Nexus contacts with emails
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM nx_contact WHERE email IS NOT NULL AND email != ''")
            nexus_contacts = rows_to_dicts(cur)

    nexus_by_email = {c["email"].lower().strip(): c for c in nexus_contacts if c.get("email")}

    # Match existing — update Nexus contacts from Outlook if title/phone missing
    for email, nc in nexus_by_email.items():
        if email in outlook_by_email:
            matched += 1
            oc = outlook_by_email[email]
            updates = {}
            if not nc.get("title") and oc.get("jobTitle"):
                updates["title"] = oc["jobTitle"]
            phones = oc.get("businessPhones", [])
            if not nc.get("phone") and phones:
                updates["phone"] = phones[0]

            if updates:
                set_clause = ", ".join(f"{k} = %s" for k in updates)
                values = list(updates.values()) + [nc["id"]]
                with get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            f"UPDATE nx_contact SET {set_clause}, updated_at = NOW() WHERE id = %s",
                            values,
                        )

    # Pull — Outlook contacts not in Nexus (create new)
    for email, oc in outlook_by_email.items():
        if email not in nexus_by_email:
            name = oc.get("displayName", email)
            title = oc.get("jobTitle")
            phones = oc.get("businessPhones", [])
            phone = phones[0] if phones else None

            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO nx_contact (name, email, title, phone, notes)
                           VALUES (%s, %s, %s, %s, 'Imported from Outlook')
                           ON CONFLICT DO NOTHING""",
                        (name, email, title, phone),
                    )
                    if cur.rowcount > 0:
                        pulled += 1

    result = {"pushed": pushed, "pulled": pulled, "matched": matched}
    logger.info("Contact sync: %s", result)
    return result
