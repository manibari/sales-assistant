"""IMAP/SMTP fallback service for non-Microsoft email accounts."""

import email
import imaplib
import logging
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from database.connection import get_connection, rows_to_dicts

logger = logging.getLogger(__name__)


def test_imap_connection(
    host: str, port: int, user: str, password: str, use_ssl: bool = True
) -> bool:
    """Test IMAP connection."""
    try:
        if use_ssl:
            conn = imaplib.IMAP4_SSL(host, port)
        else:
            conn = imaplib.IMAP4(host, port)
        conn.login(user, password)
        conn.logout()
        return True
    except Exception as e:
        logger.error("IMAP connection test failed: %s", e)
        return False


def test_smtp_connection(
    host: str, port: int, user: str, password: str, use_tls: bool = True
) -> bool:
    """Test SMTP connection."""
    try:
        if use_tls:
            server = smtplib.SMTP(host, port)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(host, port)
        server.login(user, password)
        server.quit()
        return True
    except Exception as e:
        logger.error("SMTP connection test failed: %s", e)
        return False


def fetch_imap_emails(
    host: str,
    port: int,
    user: str,
    password: str,
    use_ssl: bool = True,
    since_days: int = 7,
    max_count: int = 50,
) -> list[dict]:
    """Fetch emails via IMAP."""
    if use_ssl:
        conn = imaplib.IMAP4_SSL(host, port)
    else:
        conn = imaplib.IMAP4(host, port)

    conn.login(user, password)
    conn.select("INBOX")

    since_date = (datetime.now() - timedelta(days=since_days)).strftime("%d-%b-%Y")
    _, msg_ids = conn.search(None, f'SINCE {since_date}')
    ids = msg_ids[0].split()

    emails = []
    for msg_id in ids[-max_count:]:
        _, data = conn.fetch(msg_id, "(RFC822)")
        raw = data[0][1]
        msg = email.message_from_bytes(raw)

        body_preview = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body_preview = part.get_payload(decode=True).decode(errors="replace")[:500]
                    break
        else:
            body_preview = msg.get_payload(decode=True).decode(errors="replace")[:500]

        emails.append({
            "message_id": msg.get("Message-ID", ""),
            "subject": msg.get("Subject", ""),
            "from_addr": msg.get("From", ""),
            "to_addrs": msg.get("To", ""),
            "cc_addrs": msg.get("Cc", ""),
            "body_preview": body_preview,
            "received_at": msg.get("Date", ""),
        })

    conn.logout()
    return emails


def send_smtp_email(
    host: str,
    port: int,
    user: str,
    password: str,
    to: str,
    subject: str,
    body: str,
    use_tls: bool = True,
) -> bool:
    """Send an email via SMTP."""
    try:
        msg = MIMEMultipart()
        msg["From"] = user
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))

        if use_tls:
            server = smtplib.SMTP(host, port)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(host, port)

        server.login(user, password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        logger.error("SMTP send failed: %s", e)
        return False
