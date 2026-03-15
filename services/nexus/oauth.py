"""OAuth service — Microsoft Graph token management."""

import logging
import os
from datetime import datetime, timezone
from urllib.parse import urlencode

import httpx

from database.connection import get_connection, row_to_dict
from services.nexus.crypto import encrypt_value, decrypt_value

logger = logging.getLogger(__name__)

MICROSOFT_AUTHORITY = "https://login.microsoftonline.com"
MICROSOFT_GRAPH_SCOPES = "Mail.Read Mail.Send Calendars.ReadWrite Contacts.ReadWrite offline_access"


def _get_microsoft_config() -> dict:
    return {
        "client_id": os.getenv("MICROSOFT_CLIENT_ID", ""),
        "client_secret": os.getenv("MICROSOFT_CLIENT_SECRET", ""),
        "tenant_id": os.getenv("MICROSOFT_TENANT_ID", "common"),
        "redirect_uri": os.getenv(
            "MICROSOFT_REDIRECT_URI",
            "http://localhost:8002/api/nx/outlook/auth/callback",
        ),
    }


def get_microsoft_auth_url() -> str:
    """Generate the Microsoft OAuth authorization URL."""
    cfg = _get_microsoft_config()
    params = {
        "client_id": cfg["client_id"],
        "response_type": "code",
        "redirect_uri": cfg["redirect_uri"],
        "scope": MICROSOFT_GRAPH_SCOPES,
        "response_mode": "query",
        "prompt": "consent",
    }
    return f"{MICROSOFT_AUTHORITY}/{cfg['tenant_id']}/oauth2/v2.0/authorize?{urlencode(params)}"


def exchange_microsoft_code(code: str) -> dict:
    """Exchange authorization code for tokens and store them encrypted."""
    cfg = _get_microsoft_config()
    token_url = f"{MICROSOFT_AUTHORITY}/{cfg['tenant_id']}/oauth2/v2.0/token"

    with httpx.Client() as client:
        resp = client.post(
            token_url,
            data={
                "client_id": cfg["client_id"],
                "client_secret": cfg["client_secret"],
                "code": code,
                "redirect_uri": cfg["redirect_uri"],
                "grant_type": "authorization_code",
                "scope": MICROSOFT_GRAPH_SCOPES,
            },
        )
        resp.raise_for_status()
        token_data = resp.json()

    _store_token("microsoft_graph", token_data)
    return {"status": "connected", "provider": "microsoft_graph"}


def refresh_microsoft_token() -> dict:
    """Refresh the Microsoft access token using the stored refresh token."""
    cfg = _get_microsoft_config()
    token_url = f"{MICROSOFT_AUTHORITY}/{cfg['tenant_id']}/oauth2/v2.0/token"

    stored = _get_stored_token("microsoft_graph")
    if not stored or not stored.get("refresh_token"):
        raise ValueError("No refresh token available for microsoft_graph")

    refresh_token = decrypt_value(stored["refresh_token"])

    with httpx.Client() as client:
        resp = client.post(
            token_url,
            data={
                "client_id": cfg["client_id"],
                "client_secret": cfg["client_secret"],
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
                "scope": MICROSOFT_GRAPH_SCOPES,
            },
        )
        resp.raise_for_status()
        token_data = resp.json()

    _store_token("microsoft_graph", token_data)
    return token_data


def revoke_microsoft_token() -> None:
    """Remove stored Microsoft tokens."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM nx_oauth_token WHERE provider = 'microsoft_graph'")
            cur.execute(
                """UPDATE nx_integration_config
                   SET status = 'disconnected', updated_at = NOW()
                   WHERE provider = 'microsoft_graph'"""
            )


def get_valid_token(provider: str = "microsoft_graph") -> str:
    """Get a valid access token, refreshing if expired."""
    stored = _get_stored_token(provider)
    if not stored:
        raise ValueError(f"No token stored for {provider}")

    expires_at = stored.get("expires_at")
    if expires_at and expires_at <= datetime.now(timezone.utc):
        logger.info("Token expired for %s, refreshing...", provider)
        if provider == "microsoft_graph":
            refresh_microsoft_token()
            stored = _get_stored_token(provider)
            if not stored:
                raise ValueError("Token refresh failed")

    return decrypt_value(stored["access_token"])


def get_oauth_status(provider: str = "microsoft_graph") -> dict:
    """Check OAuth connection status."""
    stored = _get_stored_token(provider)
    if not stored:
        return {"connected": False, "provider": provider}

    return {
        "connected": True,
        "provider": provider,
        "expires_at": stored["expires_at"].isoformat() if stored.get("expires_at") else None,
        "scopes": stored.get("scopes"),
    }


# --- Internal helpers ---


def _store_token(provider: str, token_data: dict) -> None:
    """Store encrypted tokens in the database."""
    from datetime import timedelta

    access_token = encrypt_value(token_data["access_token"])
    refresh_token = (
        encrypt_value(token_data["refresh_token"]) if token_data.get("refresh_token") else None
    )
    expires_in = token_data.get("expires_in", 3600)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    scopes = token_data.get("scope", MICROSOFT_GRAPH_SCOPES)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO nx_oauth_token (provider, access_token, refresh_token, token_type, expires_at, scopes)
                   VALUES (%s, %s, %s, %s, %s, %s)
                   ON CONFLICT (provider) DO UPDATE SET
                     access_token = EXCLUDED.access_token,
                     refresh_token = COALESCE(EXCLUDED.refresh_token, nx_oauth_token.refresh_token),
                     token_type = EXCLUDED.token_type,
                     expires_at = EXCLUDED.expires_at,
                     scopes = EXCLUDED.scopes,
                     updated_at = NOW()""",
                (provider, access_token, refresh_token, token_data.get("token_type", "Bearer"), expires_at, scopes),
            )
            # Also update integration config status
            cur.execute(
                """INSERT INTO nx_integration_config (provider, enabled, status)
                   VALUES (%s, TRUE, 'connected')
                   ON CONFLICT (provider) DO UPDATE SET
                     enabled = TRUE, status = 'connected', updated_at = NOW()""",
                (provider,),
            )


def _get_stored_token(provider: str) -> dict | None:
    """Retrieve stored token from database."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM nx_oauth_token WHERE provider = %s",
                (provider,),
            )
            return row_to_dict(cur)
