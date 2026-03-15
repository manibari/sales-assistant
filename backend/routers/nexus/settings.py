"""Settings router — integration configs, AI provider, notification preferences, IMAP/SMTP."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.nexus.settings_mgr import (
    get_all_integration_configs,
    get_integration_config,
    upsert_integration_config,
    delete_integration_config,
    get_notification_preferences,
    update_notification_preferences,
    get_ai_settings,
    update_ai_settings,
    test_ai_connection,
)
from services.nexus.crypto import encrypt_value
from services.nexus.imap_smtp import (
    test_imap_connection,
    test_smtp_connection,
    fetch_imap_emails,
    send_smtp_email,
)

router = APIRouter()


# --- Pydantic models ---


class IntegrationConfigUpdate(BaseModel):
    enabled: bool | None = None
    config_json: dict | None = None


class NotificationPrefsUpdate(BaseModel):
    email_enabled: bool | None = None
    telegram_enabled: bool | None = None
    frequency: str | None = None
    events: dict | None = None


class AISettingsUpdate(BaseModel):
    provider: str
    api_key: str | None = None


class ImapSmtpConfig(BaseModel):
    imap_host: str
    imap_port: int = 993
    smtp_host: str
    smtp_port: int = 587
    username: str
    password: str
    imap_ssl: bool = True
    smtp_tls: bool = True


class ImapSmtpTestRequest(BaseModel):
    protocol: str  # "imap" or "smtp"
    host: str
    port: int
    username: str
    password: str
    use_ssl: bool = True


class SmtpSendRequest(BaseModel):
    to: str
    subject: str
    body: str


# --- Integration config ---


@router.get("/integrations")
def list_integrations():
    return get_all_integration_configs()


@router.get("/integrations/{provider}")
def get_integration(provider: str):
    config = get_integration_config(provider)
    if not config:
        raise HTTPException(status_code=404, detail=f"Integration '{provider}' not found")
    return config


@router.put("/integrations/{provider}")
def update_integration(provider: str, body: IntegrationConfigUpdate):
    return upsert_integration_config(
        provider, enabled=body.enabled, config=body.config_json
    )


@router.delete("/integrations/{provider}", status_code=204)
def remove_integration(provider: str):
    delete_integration_config(provider)


# --- Notification preferences ---


@router.get("/notifications")
def get_notifications():
    return get_notification_preferences()


@router.put("/notifications")
def update_notifications(body: NotificationPrefsUpdate):
    current = get_notification_preferences()
    if body.email_enabled is not None:
        current["email_enabled"] = body.email_enabled
    if body.telegram_enabled is not None:
        current["telegram_enabled"] = body.telegram_enabled
    if body.frequency is not None:
        current["frequency"] = body.frequency
    if body.events is not None:
        current["events"] = body.events
    return update_notification_preferences(current)


# --- AI provider ---


@router.get("/ai")
def get_ai():
    return get_ai_settings()


@router.put("/ai")
def update_ai(body: AISettingsUpdate):
    return update_ai_settings(body.provider, body.api_key)


@router.post("/ai/test")
def test_ai(body: AISettingsUpdate | None = None):
    provider = body.provider if body else None
    return test_ai_connection(provider)


# --- IMAP/SMTP ---


@router.put("/imap-smtp")
def save_imap_smtp(body: ImapSmtpConfig):
    """Save IMAP/SMTP config with encrypted password."""
    config = {
        "imap_host": body.imap_host,
        "imap_port": body.imap_port,
        "smtp_host": body.smtp_host,
        "smtp_port": body.smtp_port,
        "username": body.username,
        "password": encrypt_value(body.password),
        "imap_ssl": body.imap_ssl,
        "smtp_tls": body.smtp_tls,
    }
    return upsert_integration_config("imap_smtp", enabled=True, config=config)


@router.get("/imap-smtp")
def get_imap_smtp():
    """Get IMAP/SMTP config (password masked)."""
    config = get_integration_config("imap_smtp")
    if not config:
        return {"configured": False}
    cfg = config.get("config_json", {})
    return {
        "configured": True,
        "imap_host": cfg.get("imap_host", ""),
        "imap_port": cfg.get("imap_port", 993),
        "smtp_host": cfg.get("smtp_host", ""),
        "smtp_port": cfg.get("smtp_port", 587),
        "username": cfg.get("username", ""),
        "has_password": bool(cfg.get("password")),
        "imap_ssl": cfg.get("imap_ssl", True),
        "smtp_tls": cfg.get("smtp_tls", True),
        "status": config.get("status", "disconnected"),
    }


@router.post("/imap-smtp/test")
def test_imap_smtp_connection(body: ImapSmtpTestRequest):
    """Test IMAP or SMTP connection."""
    try:
        # If password is placeholder, use stored password
        pwd = body.password
        if pwd == "___USE_STORED___":
            config = get_integration_config("imap_smtp")
            if not config:
                raise HTTPException(status_code=400, detail="No stored config found")
            from services.nexus.crypto import decrypt_value
            pwd = decrypt_value(config["config_json"]["password"])

        if body.protocol == "imap":
            ok = test_imap_connection(body.host, body.port, body.username, pwd, body.use_ssl)
        elif body.protocol == "smtp":
            ok = test_smtp_connection(body.host, body.port, body.username, pwd, body.use_ssl)
        else:
            raise HTTPException(status_code=400, detail="protocol must be 'imap' or 'smtp'")

        if ok:
            from services.nexus.settings_mgr import update_integration_status
            update_integration_status("imap_smtp", "connected")

        return {"success": ok, "protocol": body.protocol}
    except Exception as e:
        return {"success": False, "protocol": body.protocol, "error": str(e)}


@router.post("/imap-smtp/fetch")
def fetch_imap(days: int = 7, max_count: int = 50):
    """Fetch emails via IMAP and store in DB."""
    config = get_integration_config("imap_smtp")
    if not config:
        raise HTTPException(status_code=400, detail="IMAP not configured")
    cfg = config.get("config_json", {})

    from services.nexus.crypto import decrypt_value
    password = decrypt_value(cfg["password"])

    emails = fetch_imap_emails(
        host=cfg["imap_host"],
        port=cfg["imap_port"],
        user=cfg["username"],
        password=password,
        use_ssl=cfg.get("imap_ssl", True),
        since_days=days,
        max_count=max_count,
    )

    # Store to nx_email_thread
    import json
    from database.connection import get_connection
    synced = 0
    with get_connection() as conn:
        with conn.cursor() as cur:
            for em in emails:
                cur.execute(
                    """INSERT INTO nx_email_thread
                       (message_id, subject, from_addr, to_addrs, cc_addrs,
                        body_preview, direction, received_at)
                       VALUES (%s, %s, %s, %s, %s, %s, 'inbound', %s)
                       ON CONFLICT (message_id) DO NOTHING""",
                    (
                        em["message_id"],
                        em["subject"],
                        em["from_addr"],
                        em["to_addrs"],
                        em["cc_addrs"],
                        em["body_preview"],
                        em["received_at"],
                    ),
                )
                if cur.rowcount > 0:
                    synced += 1

    # Auto-associate
    from services.nexus.outlook import auto_associate_emails
    auto_associate_emails()

    return {"fetched": len(emails), "new": synced}


@router.post("/imap-smtp/send")
def send_via_smtp(body: SmtpSendRequest):
    """Send email via SMTP."""
    config = get_integration_config("imap_smtp")
    if not config:
        raise HTTPException(status_code=400, detail="SMTP not configured")
    cfg = config.get("config_json", {})

    from services.nexus.crypto import decrypt_value
    password = decrypt_value(cfg["password"])

    ok = send_smtp_email(
        host=cfg["smtp_host"],
        port=cfg["smtp_port"],
        user=cfg["username"],
        password=password,
        to=body.to,
        subject=body.subject,
        body=body.body,
        use_tls=cfg.get("smtp_tls", True),
    )
    if not ok:
        raise HTTPException(status_code=500, detail="SMTP send failed")
    return {"status": "sent"}
