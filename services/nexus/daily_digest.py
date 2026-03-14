"""Daily digest — gather all actionable items into a formatted report."""

from datetime import date

from database.connection import get_connection, rows_to_dicts
from services.nexus.calendar import get_meetings_by_date, get_pending_reminders
from services.nexus.deals import get_deals_needing_push
from services.nexus.documents import get_expiring_documents
from services.nexus.intel import get_all_intel
from services.nexus.tbd import get_open_tbds


def build_daily_digest() -> dict:
    """Gather all daily to-do items. Returns structured data."""
    today = date.today().isoformat()

    # 1. Today's meetings
    meetings = get_meetings_by_date(today)

    # 2. Overdue/due reminders
    reminders = get_pending_reminders()

    # 3. Open TBDs
    tbds = get_open_tbds()

    # 4. Idle deals needing push (>14 days)
    idle_deals = get_deals_needing_push(threshold_days=14)

    # 5. Draft intel (unconfirmed)
    draft_intel = get_all_intel(status="draft", limit=20)

    # 6. Expiring documents (within 30 days)
    expiring_docs = get_expiring_documents(within_days=30)

    # 7. Upcoming meetings (next 3 days)
    upcoming = _get_upcoming_meetings(today, days=3)

    return {
        "date": today,
        "meetings_today": meetings,
        "upcoming_meetings": upcoming,
        "reminders": reminders,
        "open_tbds": tbds,
        "idle_deals": idle_deals,
        "draft_intel": draft_intel,
        "expiring_docs": expiring_docs,
    }


def format_digest_telegram(data: dict) -> str:
    """Format digest as Telegram-friendly text (HTML parse_mode)."""
    lines = [f"📋 <b>每日待辦 — {data['date']}</b>"]

    # Today's meetings
    meetings = data["meetings_today"]
    if meetings:
        lines.append("")
        lines.append(f"📅 <b>今日會議 ({len(meetings)})</b>")
        for m in meetings:
            time_str = m["meeting_date"][11:16] if len(m["meeting_date"]) > 10 else ""
            lines.append(f"  • {time_str} {m['title']} — {m.get('client_name', '')}")
    else:
        lines.append("")
        lines.append("📅 今日無會議")

    # Upcoming meetings (next 3 days)
    upcoming = data["upcoming_meetings"]
    if upcoming:
        lines.append("")
        lines.append(f"🗓 <b>近期會議 ({len(upcoming)})</b>")
        for m in upcoming:
            date_str = m["meeting_date"][:10]
            time_str = m["meeting_date"][11:16] if len(m["meeting_date"]) > 10 else ""
            lines.append(f"  • {date_str} {time_str} {m['title']}")

    # Reminders
    reminders = data["reminders"]
    if reminders:
        lines.append("")
        lines.append(f"⏰ <b>待處理提醒 ({len(reminders)})</b>")
        for r in reminders[:5]:
            deal_name = r.get("deal_name", "")
            lines.append(f"  • {r['content']}" + (f" ({deal_name})" if deal_name else ""))
        if len(reminders) > 5:
            lines.append(f"  ...還有 {len(reminders) - 5} 項")

    # Idle deals
    idle = data["idle_deals"]
    if idle:
        lines.append("")
        lines.append(f"🔴 <b>需推進案件 ({len(idle)})</b>")
        for d in idle[:5]:
            lines.append(
                f"  • {d.get('client_name', '')} — {d['name']} "
                f"(閒置 {d.get('idle_days', '?')} 天, {d['stage']})"
            )
        if len(idle) > 5:
            lines.append(f"  ...還有 {len(idle) - 5} 件")

    # Open TBDs
    tbds = data["open_tbds"]
    if tbds:
        lines.append("")
        lines.append(f"❓ <b>待確認事項 ({len(tbds)})</b>")
        for t in tbds[:5]:
            lines.append(f"  • {t['question']}")
        if len(tbds) > 5:
            lines.append(f"  ...還有 {len(tbds) - 5} 項")

    # Draft intel
    drafts = data["draft_intel"]
    if drafts:
        lines.append("")
        lines.append(f"📝 <b>未確認情報 ({len(drafts)})</b>")
        for i in drafts[:3]:
            preview = (i.get("title") or i["raw_input"])[:40].replace("\n", " ")
            lines.append(f"  • #{i['id']} {preview}...")
        if len(drafts) > 3:
            lines.append(f"  ...還有 {len(drafts) - 3} 筆")

    # Expiring documents
    expiring = data["expiring_docs"]
    if expiring:
        lines.append("")
        lines.append(f"📄 <b>即將到期文件 ({len(expiring)})</b>")
        for doc in expiring[:3]:
            lines.append(
                f"  • {doc.get('client_name', '')} {doc['doc_type'].upper()} "
                f"到期：{doc.get('expiry_date', '?')}"
            )

    # Summary count
    total = (
        len(meetings) + len(reminders) + len(idle) + len(tbds) + len(drafts) + len(expiring)
    )
    if total == 0:
        lines.append("")
        lines.append("✅ 今天沒有待辦事項，太厲害了！")
    else:
        lines.append("")
        lines.append(f"共 {total} 項待處理")

    return "\n".join(lines)


def _get_upcoming_meetings(today: str, days: int = 3) -> list[dict]:
    """Get meetings in the next N days (excluding today)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT m.*, d.name AS deal_name, c.name AS client_name
                   FROM nx_meeting m
                   JOIN nx_deal d ON m.deal_id = d.id
                   JOIN nx_client c ON d.client_id = c.id
                   WHERE m.meeting_date::DATE > %s::DATE
                     AND m.meeting_date::DATE <= (%s::DATE + %s * INTERVAL '1 day')::DATE
                     AND m.status = 'scheduled'
                   ORDER BY m.meeting_date ASC""",
                (today, today, days),
            )
            return rows_to_dicts(cur)
