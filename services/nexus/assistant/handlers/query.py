"""Query handlers — search clients, deals, tenders, schedule, subsidies.

These handlers query existing data and return formatted results.
"""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import date, timedelta

from services.nexus.assistant.intents import Intent

logger = logging.getLogger(__name__)


async def handle_query(text: str, intent: Intent) -> "AssistantResponse":
    """Route to the appropriate query handler."""
    from services.nexus.assistant.engine import AssistantResponse

    match intent:
        case Intent.QUERY_CLIENT:
            return await _query_client(text)
        case Intent.QUERY_DEAL:
            return await _query_deal(text)
        case Intent.QUERY_TENDER:
            return await _query_tender(text)
        case Intent.QUERY_SUBSIDY:
            return await _query_subsidy(text)
        case Intent.QUERY_SCHEDULE:
            return await _query_schedule(text)
        case _:
            return await _query_general(text)


async def handle_today() -> "AssistantResponse":
    """Send daily digest."""
    from services.nexus.assistant.engine import AssistantResponse
    from services.nexus.daily_digest import build_daily_digest, format_digest_telegram

    data = await asyncio.to_thread(build_daily_digest)
    text = format_digest_telegram(data)
    return AssistantResponse(text=text, intent=Intent.QUERY_SCHEDULE)


# ---------------------------------------------------------------------------
# Individual query handlers
# ---------------------------------------------------------------------------


def _extract_company_name(text: str) -> str:
    """Extract company name from query text like '查 美珍香' or '美珍香 最近怎樣'."""
    # Remove query keywords
    cleaned = re.sub(
        r"^(?:查|找|看|搜尋|搜|列出)\s*", "", text.strip()
    )
    cleaned = re.sub(
        r"\s*(?:最近怎[樣麼]|的?狀況|的?情況|怎[樣麼]|進度)$", "", cleaned
    )
    return cleaned.strip()


async def _query_client(text: str) -> "AssistantResponse":
    """Search for a client and return their info + recent activity."""
    from services.nexus.assistant.engine import AssistantResponse
    from services.nexus.clients import find_client_by_name
    from services.nexus.deals import get_deals_by_client
    from services.nexus.contacts import get_contacts_by_org

    name = _extract_company_name(text)
    if not name:
        return AssistantResponse(
            text="請告訴我要查哪家公司，例如「查 美珍香」",
            intent=Intent.QUERY_CLIENT,
        )

    clients = await asyncio.to_thread(find_client_by_name, name)
    if not clients:
        return AssistantResponse(
            text=f"找不到「{name}」相關的客戶。請確認名稱或輸入更完整的公司名。",
            intent=Intent.QUERY_CLIENT,
            suggestions=[f"查 {name}的完整名稱"],
        )

    client = clients[0]
    lines = [f"🏢 {client['name']}"]
    if client.get("industry"):
        lines[0] += f"（{client['industry']}）"
    if client.get("region"):
        lines.append(f"📍 {client['region']}")

    # Get contacts
    contacts = await asyncio.to_thread(get_contacts_by_org, "client", client["id"])
    if contacts:
        contact_strs = []
        for c in contacts[:3]:
            s = c["name"]
            if c.get("title"):
                s += f"（{c['title']}）"
            contact_strs.append(s)
        lines.append(f"👤 聯絡人：{'、'.join(contact_strs)}")

    # Get deals
    deals = await asyncio.to_thread(get_deals_by_client, client["id"])
    if deals:
        active = [d for d in deals if d.get("status") == "active"]
        if active:
            lines.append(f"\n💼 進行中商機（{len(active)} 筆）：")
            for d in active[:5]:
                stage = d.get("stage", "?")
                lines.append(f"  • {d['name']}（{stage}）")
    else:
        lines.append("\n💼 目前無商機")

    return AssistantResponse(
        text="\n".join(lines),
        intent=Intent.QUERY_CLIENT,
        card_data={"type": "client", "client": client, "deals": deals or []},
    )


async def _query_deal(text: str) -> "AssistantResponse":
    """Search for deals."""
    from services.nexus.assistant.engine import AssistantResponse
    from services.nexus.deals import get_deals_by_urgency

    deals = await asyncio.to_thread(get_deals_by_urgency)
    if not deals:
        return AssistantResponse(
            text="目前沒有進行中的商機。",
            intent=Intent.QUERY_DEAL,
        )

    # Filter by text if specific deal/company mentioned
    name = _extract_company_name(text)
    if name:
        matched = [
            d for d in deals
            if name.lower() in (d.get("name", "") + d.get("client_name", "")).lower()
        ]
        if matched:
            deals = matched

    lines = [f"💼 商機列表（{len(deals)} 筆）："]
    for d in deals[:10]:
        stage = d.get("stage", "?")
        client = d.get("client_name", "")
        name_str = d["name"]
        if client and client not in name_str:
            name_str = f"{client} — {name_str}"
        lines.append(f"  • {name_str}（{stage}）")

    return AssistantResponse(
        text="\n".join(lines),
        intent=Intent.QUERY_DEAL,
        card_data={"type": "deals", "deals": deals[:10]},
    )


async def _query_tender(text: str) -> "AssistantResponse":
    """List active/expiring tenders."""
    from services.nexus.assistant.engine import AssistantResponse
    from services.nexus.tenders import get_tenders_expiring

    tenders = await asyncio.to_thread(get_tenders_expiring, 30)
    if not tenders:
        return AssistantResponse(
            text="近 30 天內沒有即將到期的標案。",
            intent=Intent.QUERY_TENDER,
        )

    lines = [f"📋 近期標案（{len(tenders)} 筆）："]
    for t in tenders[:10]:
        deadline = t.get("deadline", "?")
        lines.append(f"  • {t['title']}（截止：{deadline}）")

    return AssistantResponse(
        text="\n".join(lines),
        intent=Intent.QUERY_TENDER,
        card_data={"type": "tenders", "tenders": tenders[:10]},
    )


async def _query_subsidy(text: str) -> "AssistantResponse":
    """List subsidies."""
    from services.nexus.assistant.engine import AssistantResponse
    from services.nexus.subsidies import get_all_subsidies

    try:
        subsidies = await asyncio.to_thread(get_all_subsidies, "active", 10)
    except Exception:
        subsidies = []

    if not subsidies:
        return AssistantResponse(
            text="目前沒有追蹤中的補助資訊。",
            intent=Intent.QUERY_SUBSIDY,
        )

    lines = [f"📋 補助列表（{len(subsidies)} 筆）："]
    for s in subsidies[:10]:
        deadline = s.get("deadline", "?")
        lines.append(f"  • {s.get('name', s.get('title', '?'))}（截止：{deadline}）")

    return AssistantResponse(
        text="\n".join(lines),
        intent=Intent.QUERY_SUBSIDY,
    )


async def _query_schedule(text: str) -> "AssistantResponse":
    """Show today's or this week's schedule."""
    from services.nexus.assistant.engine import AssistantResponse

    try:
        from services.nexus.calendar import get_meetings_by_range

        today = date.today()

        # Check if asking about this week
        is_week = any(w in text for w in ("這週", "本週", "this week"))
        if is_week:
            start = today
            end = today + timedelta(days=7)
            label = "本週"
        else:
            start = today
            end = today
            label = "今天"

        meetings = await asyncio.to_thread(
            get_meetings_by_range, start.isoformat(), end.isoformat()
        )

        if not meetings:
            return AssistantResponse(
                text=f"📅 {label}沒有排定的會議。",
                intent=Intent.QUERY_SCHEDULE,
            )

        lines = [f"📅 {label}的行程（{len(meetings)} 筆）："]
        for m in meetings[:10]:
            time_str = m.get("start_time", "")
            title = m.get("title", "")
            client = m.get("client_name", "")
            line = f"  • {time_str} {title}"
            if client:
                line += f"（{client}）"
            lines.append(line)

        return AssistantResponse(
            text="\n".join(lines),
            intent=Intent.QUERY_SCHEDULE,
            card_data={"type": "schedule", "meetings": meetings[:10]},
        )
    except ImportError:
        return AssistantResponse(
            text="📅 行事曆模組尚未啟用。",
            intent=Intent.QUERY_SCHEDULE,
        )
    except Exception as e:
        logger.warning("Schedule query failed: %s", e)
        return AssistantResponse(
            text=f"📅 查詢行程失敗：{e}",
            intent=Intent.QUERY_SCHEDULE,
        )


async def _query_general(text: str) -> "AssistantResponse":
    """General query — try search service."""
    from services.nexus.assistant.engine import AssistantResponse

    try:
        from services.nexus.search import search_all

        results = await asyncio.to_thread(search_all, text)
        if not results:
            return AssistantResponse(
                text=f"找不到「{text}」相關的資料。",
                intent=Intent.QUERY_GENERAL,
            )

        lines = [f"🔍 搜尋「{text}」的結果："]
        for r in results[:5]:
            lines.append(f"  • [{r.get('type', '?')}] {r.get('title', r.get('name', '?'))}")

        return AssistantResponse(
            text="\n".join(lines),
            intent=Intent.QUERY_GENERAL,
        )
    except Exception:
        return AssistantResponse(
            text=f"搜尋「{text}」時發生錯誤，請稍後再試。",
            intent=Intent.QUERY_GENERAL,
        )
