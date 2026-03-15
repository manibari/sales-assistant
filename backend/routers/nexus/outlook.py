"""Outlook router — OAuth flow, email CRUD, sync."""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from services.nexus.oauth import (
    get_microsoft_auth_url,
    exchange_microsoft_code,
    revoke_microsoft_token,
    get_oauth_status,
    get_valid_token,
)
from services.nexus.outlook import (
    fetch_inbox,
    get_email,
    send_email,
    reply_email,
    sync_emails_to_db,
    get_emails,
    get_email_by_id,
)
from services.nexus.outlook_calendar import (
    sync_meetings_to_outlook,
    sync_outlook_to_meetings,
)
from services.nexus.outlook_contacts import sync_contacts_bidirectional

router = APIRouter()


# --- Pydantic models ---


class SendEmailRequest(BaseModel):
    to: list[str]
    subject: str
    body: str


class ReplyEmailRequest(BaseModel):
    body: str


# --- OAuth flow ---


@router.get("/auth/url")
def auth_url():
    """Get the Microsoft OAuth authorization URL."""
    url = get_microsoft_auth_url()
    return {"url": url}


@router.get("/auth/callback", response_class=HTMLResponse)
def auth_callback(code: str = Query(...)):
    """Handle OAuth callback from Microsoft."""
    try:
        exchange_microsoft_code(code)
        # Return HTML that notifies the opener window and closes
        return HTMLResponse(
            content="""
            <html>
            <body>
            <h2>Authorization successful!</h2>
            <p>You can close this window.</p>
            <script>
                if (window.opener) {
                    window.opener.postMessage("oauth_complete", "*");
                }
                setTimeout(() => window.close(), 2000);
            </script>
            </body>
            </html>
            """
        )
    except Exception as e:
        return HTMLResponse(
            content=f"""
            <html>
            <body>
            <h2>Authorization failed</h2>
            <p>{str(e)}</p>
            <script>
                if (window.opener) {{
                    window.opener.postMessage("oauth_error", "*");
                }}
            </script>
            </body>
            </html>
            """,
            status_code=400,
        )


@router.post("/auth/disconnect")
def disconnect():
    """Revoke Microsoft OAuth tokens."""
    revoke_microsoft_token()
    return {"status": "disconnected"}


@router.get("/auth/status")
def auth_status():
    """Check Microsoft OAuth connection status."""
    return get_oauth_status()


# --- Email endpoints ---


@router.get("/emails")
def list_emails(
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
):
    """List synced emails."""
    return get_emails(limit=limit, offset=offset)


@router.get("/emails/by-client/{client_id}")
def emails_by_client(
    client_id: int,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
):
    return get_emails(client_id=client_id, limit=limit, offset=offset)


@router.get("/emails/by-deal/{deal_id}")
def emails_by_deal(
    deal_id: int,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
):
    return get_emails(deal_id=deal_id, limit=limit, offset=offset)


@router.get("/emails/{email_id}")
def get_single_email(email_id: int):
    """Get a single email by database ID."""
    email = get_email_by_id(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return email


@router.post("/emails/send")
def send(body: SendEmailRequest):
    """Send an email via Microsoft Graph."""
    try:
        token = get_valid_token()
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    return send_email(token, body.to, body.subject, body.body)


@router.post("/emails/{message_id}/reply")
def reply(message_id: str, body: ReplyEmailRequest):
    """Reply to an email."""
    try:
        token = get_valid_token()
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    return reply_email(token, message_id, body.body)


@router.post("/emails/sync")
def sync():
    """Manually trigger email sync from Microsoft Graph."""
    try:
        token = get_valid_token()
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    count = sync_emails_to_db(token)
    return {"synced": count}


# --- Calendar sync (Phase C) ---


@router.post("/calendar/sync")
def calendar_sync():
    """Bidirectional calendar sync with Outlook."""
    try:
        token = get_valid_token()
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    pushed = sync_meetings_to_outlook(token)
    pulled = sync_outlook_to_meetings(token)
    return {"pushed_to_outlook": pushed, "pulled_from_outlook": pulled}


# --- Contacts sync (Phase C) ---


@router.post("/contacts/sync")
def contacts_sync():
    """Bidirectional contact sync with Outlook."""
    try:
        token = get_valid_token()
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    result = sync_contacts_bidirectional(token)
    return result
