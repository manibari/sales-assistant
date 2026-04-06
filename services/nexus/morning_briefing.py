"""Morning Briefing — proactive daily push via Telegram.

Sends a concise action-oriented briefing to all registered Telegram chats
every morning (default: 08:30 local time).

The briefing flips the system from "passive database" to "active assistant":
instead of users going to check the dashboard, the system finds them.
"""

import logging
import os
from datetime import date

import httpx

from services.nexus.daily_digest import build_daily_digest

_logger = logging.getLogger(__name__)


def _bot_token() -> str:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not set")
    return token


def _load_registered_chats() -> set[int]:
    """Load persisted chat IDs (reuse the same file as telegram router)."""
    path = os.getenv("TELEGRAM_CHATS_FILE", "/tmp/tg_registered_chats.json")
    try:
        import json
        with open(path) as f:
            return set(json.load(f))
    except Exception:
        return set()


def format_morning_briefing(data: dict) -> str:
    """Opinionated morning briefing format — priorities first, concise."""
    today = date.today().strftime("%m/%d %A")
    lines = [f"☀️ <b>早安！今天 {today}</b>"]

    # Priority 1: Today's meetings (time-sensitive)
    meetings = data.get("meetings_today", [])
    if meetings:
        lines.append("")
        lines.append(f"📅 <b>今日會議 {len(meetings)} 場</b>")
        for m in meetings[:5]:
            time_str = m["meeting_date"][11:16] if len(m["meeting_date"]) > 10 else ""
            client = m.get("client_name", "")
            lines.append(f"  {time_str} · {m['title']}" + (f" ({client})" if client else ""))

    # Priority 2: Idle deals (most actionable)
    idle = data.get("idle_deals", [])
    if idle:
        lines.append("")
        lines.append(f"🔴 <b>需要跟進 {len(idle)} 件</b>")
        for d in idle[:4]:
            client = d.get("client_name", "")
            idle_days = d.get("idle_days", "?")
            lines.append(f"  • {client} — {d['name']} (閒置 {idle_days} 天)")
        if len(idle) > 4:
            lines.append(f"  ...還有 {len(idle) - 4} 件")

    # Priority 3: Expiring documents (deadline-driven)
    expiring = data.get("expiring_docs", [])
    if expiring:
        lines.append("")
        lines.append(f"📄 <b>文件即將到期 {len(expiring)} 份</b>")
        for doc in expiring[:3]:
            client = doc.get("client_name", "")
            lines.append(
                f"  • {client} {doc['doc_type'].upper()} 到期：{doc.get('expiry_date', '?')}"
            )

    # Priority 4: Overdue reminders
    reminders = data.get("reminders", [])
    if reminders:
        lines.append("")
        lines.append(f"⏰ <b>待處理提醒 {len(reminders)} 項</b>")
        for r in reminders[:3]:
            lines.append(f"  • {r['content']}")
        if len(reminders) > 3:
            lines.append(f"  ...還有 {len(reminders) - 3} 項")

    # If everything is clear
    total = len(meetings) + len(idle) + len(expiring) + len(reminders)
    if total == 0:
        lines.append("")
        lines.append("✅ 今天暫無待辦，繼續保持！")
    else:
        lines.append("")
        lines.append(f"共 {total} 項需要注意")

    return "\n".join(lines)


async def send_morning_briefing_async() -> dict:
    """Build and push briefing to all registered Telegram chats. Returns stats."""
    try:
        token = _bot_token()
    except ValueError as e:
        _logger.warning("Morning briefing skipped: %s", e)
        return {"skipped": True, "reason": str(e)}

    chats = _load_registered_chats()
    if not chats:
        _logger.info("Morning briefing: no registered chats, skipping")
        return {"skipped": True, "reason": "no registered chats"}

    data = build_daily_digest()
    text = format_morning_briefing(data)
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    sent, failed = 0, 0
    async with httpx.AsyncClient(timeout=15) as client:
        for chat_id in chats:
            try:
                r = await client.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})
                if r.status_code == 200:
                    sent += 1
                else:
                    _logger.warning("Telegram sendMessage failed for %d: %s", chat_id, r.text)
                    failed += 1
            except Exception as e:
                _logger.warning("Telegram send error for chat %d: %s", chat_id, e)
                failed += 1

    _logger.info("Morning briefing sent to %d chats (%d failed)", sent, failed)
    return {"sent": sent, "failed": failed, "date": data["date"]}


def send_morning_briefing_sync() -> dict:
    """Sync wrapper for use in background threads."""
    import asyncio
    return asyncio.run(send_morning_briefing_async())
