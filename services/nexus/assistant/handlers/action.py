"""Action handlers — create deals, meetings, reminders; update deals; generate pitches.

These handlers perform write operations and return confirmation.
Supports multi-turn conversation for collecting missing information.
"""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import date, datetime, timedelta

from services.nexus.assistant.intents import Intent

logger = logging.getLogger(__name__)


async def handle_action(
    engine: "AssistantEngine",
    session_id: str,
    text: str,
    intent: Intent,
    entities: dict | None = None,
) -> "AssistantResponse":
    """Route to the appropriate action handler."""
    from services.nexus.assistant.engine import AssistantResponse

    entities = entities or {}

    match intent:
        case Intent.ACTION_CREATE_DEAL:
            return await _action_create_deal(text)
        case Intent.ACTION_CREATE_MEETING:
            return await _action_create_meeting(engine, session_id, text, entities)
        case Intent.ACTION_CREATE_REMINDER:
            return await _action_create_reminder(text)
        case Intent.ACTION_UPDATE_DEAL:
            return await _action_update_deal(text)
        case Intent.ACTION_GENERATE_PITCH:
            return await _action_generate_pitch(text)
        case _:
            return AssistantResponse(
                text="⚠️ 這個動作我還不支援，請稍後再試。",
                intent=intent,
            )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_company_from_text(text: str) -> str | None:
    """Try to extract a company name from action text."""
    # "幫美珍香建一個案子" → "美珍香"
    # "排3/28跟台積電開會" → "台積電"
    patterns = [
        r"(?:幫|替|為)\s*(\S{2,}?)\s*(?:建|開|新增)",
        r"(?:跟|和|與)\s*(\S{2,}?)\s*(?:開會|meeting|會議)",
        r"(\S{2,}?)\s*(?:的案子|的商機)",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1)
    return None


def _resolve_date(date_str: str | None) -> str | None:
    """Resolve a date string from LLM entities to YYYY-MM-DD format.

    Handles: '今天', '明天', '後天', '下週X', 'M/D', 'YYYY-MM-DD', etc.
    """
    if not date_str:
        return None

    today = date.today()
    d = date_str.strip()

    if d in ("今天", "今日"):
        return today.isoformat()
    if d in ("明天", "明日"):
        return (today + timedelta(days=1)).isoformat()
    if d in ("後天",):
        return (today + timedelta(days=2)).isoformat()

    # "下週一" ... "下週日"
    weekday_map = {"一": 0, "二": 1, "三": 2, "四": 3, "五": 4, "六": 5, "日": 6, "天": 6}
    m = re.match(r"(?:下週|下周)([一二三四五六日天])", d)
    if m:
        target_wd = weekday_map[m.group(1)]
        days_ahead = (target_wd - today.weekday() + 7) % 7
        if days_ahead == 0:
            days_ahead = 7
        return (today + timedelta(days=days_ahead)).isoformat()

    # M/D format (e.g., "3/28")
    m = re.match(r"(\d{1,2})/(\d{1,2})", d)
    if m:
        month, day = int(m.group(1)), int(m.group(2))
        year = today.year
        try:
            result = date(year, month, day)
            if result < today:
                result = date(year + 1, month, day)
            return result.isoformat()
        except ValueError:
            return None

    # Already YYYY-MM-DD
    m = re.match(r"\d{4}-\d{2}-\d{2}", d)
    if m:
        return m.group(0)

    return None


def _resolve_time(time_str: str | None) -> str | None:
    """Resolve a time string to HH:MM format.

    Handles: '下午兩點', '14:00', '上午九點半', etc.
    """
    if not time_str:
        return None

    t = time_str.strip()

    # Already HH:MM
    m = re.match(r"(\d{1,2}):(\d{2})", t)
    if m:
        return f"{int(m.group(1)):02d}:{m.group(2)}"

    # Chinese number mapping
    cn_nums = {"一": 1, "二": 2, "兩": 2, "三": 3, "四": 4, "五": 5, "六": 6,
               "七": 7, "八": 8, "九": 9, "十": 10, "十一": 11, "十二": 12}

    is_pm = "下午" in t or "晚上" in t
    is_am = "上午" in t or "早上" in t

    # "X點半" or "X點"
    m = re.search(r"(\d+|[一二兩三四五六七八九十]+)點(?:半)?", t)
    if m:
        hour_str = m.group(1)
        hour = cn_nums.get(hour_str) or int(hour_str)
        minute = 30 if "半" in t else 0
        if is_pm and hour < 12:
            hour += 12
        if is_am and hour == 12:
            hour = 0
        return f"{hour:02d}:{minute:02d}"

    return None


# ---------------------------------------------------------------------------
# Action handlers
# ---------------------------------------------------------------------------


async def _action_create_deal(text: str) -> "AssistantResponse":
    """Create a new deal from natural language."""
    from services.nexus.assistant.engine import AssistantResponse
    from services.nexus.clients import find_client_by_name
    from services.nexus.deals import create_deal

    company = _extract_company_from_text(text)
    if not company:
        return AssistantResponse(
            text="請告訴我要為哪家公司建案子，例如「幫美珍香建案子」",
            intent=Intent.ACTION_CREATE_DEAL,
        )

    clients = await asyncio.to_thread(find_client_by_name, company)
    if not clients:
        return AssistantResponse(
            text=f"找不到「{company}」這個客戶。要先建立客戶嗎？或確認名稱是否正確。",
            intent=Intent.ACTION_CREATE_DEAL,
        )

    client = clients[0]
    deal_name = f"{client['name']} — 新商機"

    try:
        deal = await asyncio.to_thread(
            create_deal, name=deal_name, client_id=client["id"]
        )
        return AssistantResponse(
            text=(
                f"💼 已建立商機「{deal_name}」(#{deal['id']})\n"
                f"客戶：{client['name']}\n"
                f"階段：L0\n\n"
                f"可以繼續補充預算、時程等資訊"
            ),
            intent=Intent.ACTION_CREATE_DEAL,
            actions_taken=[{"type": "create_deal", "id": deal["id"], "name": deal_name}],
        )
    except Exception as e:
        logger.error("Create deal failed: %s", e)
        return AssistantResponse(
            text=f"⚠️ 建立商機失敗：{e}",
            intent=Intent.ACTION_CREATE_DEAL,
        )


async def _action_create_meeting(
    engine: "AssistantEngine",
    session_id: str,
    text: str,
    entities: dict,
) -> "AssistantResponse":
    """Create a meeting from natural language with multi-turn collection."""
    from services.nexus.assistant.engine import AssistantResponse

    # Check if we have an active meeting-creation session
    session = engine.sessions.get(session_id)
    if session and session.intent == Intent.ACTION_CREATE_MEETING:
        # Continue collecting — merge new entities
        session.merge_fields(entities)
        # Also try to parse info from the raw text reply
        _enrich_meeting_entities_from_text(text, session.parsed)
        entities = session.parsed
    else:
        # First message — try to extract entities from text + LLM entities
        _enrich_meeting_entities_from_text(text, entities)

    # Resolve date/time
    resolved_date = _resolve_date(entities.get("date"))
    resolved_time = _resolve_time(entities.get("time"))

    # Check what's missing
    title = entities.get("title") or entities.get("description") or entities.get("company")
    missing = []
    if not title:
        missing.append("會議內容或標題")
    if not resolved_date:
        missing.append("日期")
    if not resolved_time:
        missing.append("時間")

    if missing:
        # Create or reuse session for multi-turn collection
        if not session or session.intent != Intent.ACTION_CREATE_MEETING:
            session = engine.sessions.create(
                session_id, intent=Intent.ACTION_CREATE_MEETING
            )
            # Store a sentinel so has_active works — use -1 as "no intel"
            session.intel_id = -1
        session.parsed = entities
        session.parsed["_resolved_date"] = resolved_date
        session.parsed["_resolved_time"] = resolved_time
        if title:
            session.parsed["title"] = title

        collected_parts = []
        if title:
            collected_parts.append(f"標題：{title}")
        if resolved_date:
            collected_parts.append(f"日期：{resolved_date}")
        if resolved_time:
            collected_parts.append(f"時間：{resolved_time}")

        prompt = f"好的，要新增行程。請告訴我：{'、'.join(missing)}"
        if collected_parts:
            prompt = f"收到。{'｜'.join(collected_parts)}\n還需要：{'、'.join(missing)}"

        return AssistantResponse(
            text=prompt,
            intent=Intent.ACTION_CREATE_MEETING,
        )

    # All info collected — create the meeting
    # Close session if active
    engine.sessions.close(session_id)

    meeting_datetime = f"{resolved_date}T{resolved_time}:00"

    # Try to find client
    company = entities.get("company")
    client_id = None
    client_name = ""
    if company:
        try:
            from services.nexus.clients import find_client_by_name
            clients = await asyncio.to_thread(find_client_by_name, company)
            if clients:
                client_id = clients[0]["id"]
                client_name = clients[0]["name"]
        except Exception:
            pass

    # Find deal_id if we have a client
    deal_id = None
    if client_id:
        try:
            from services.nexus.deals import get_deals_by_client
            deals = await asyncio.to_thread(get_deals_by_client, client_id)
            if deals:
                deal_id = deals[0]["id"]
        except Exception:
            pass

    try:
        from services.nexus.calendar import create_meeting

        meeting = await asyncio.to_thread(
            create_meeting,
            title=title,
            meeting_date=meeting_datetime,
            deal_id=deal_id,
        )

        result_text = (
            f"📅 已建立行程\n"
            f"標題：{title}\n"
            f"時間：{resolved_date} {resolved_time}\n"
        )
        if client_name:
            result_text += f"客戶：{client_name}\n"

        return AssistantResponse(
            text=result_text,
            intent=Intent.ACTION_CREATE_MEETING,
            actions_taken=[{"type": "create_meeting", "id": meeting.get("id")}],
        )
    except Exception as e:
        logger.error("Create meeting failed: %s", e)
        return AssistantResponse(
            text=f"⚠️ 建立行程失敗：{e}",
            intent=Intent.ACTION_CREATE_MEETING,
        )


def _enrich_meeting_entities_from_text(text: str, entities: dict) -> None:
    """Try to extract meeting-related info from raw text into entities dict."""
    # Company extraction
    if "company" not in entities:
        company = _extract_company_from_text(text)
        if company:
            entities["company"] = company

    # Date patterns from text (if LLM didn't extract)
    if "date" not in entities:
        for pattern, value in [
            (r"今[天日]", "今天"),
            (r"明[天日]", "明天"),
            (r"後天", "後天"),
            (r"下[週周][一二三四五六日天]", None),  # handled below
            (r"\d{1,2}/\d{1,2}", None),
        ]:
            m = re.search(pattern, text)
            if m:
                entities["date"] = value or m.group(0)
                break

    # Time patterns from text (if LLM didn't extract)
    if "time" not in entities:
        time_patterns = [
            r"\d{1,2}:\d{2}",
            r"(?:上午|下午|早上|晚上)?[一二兩三四五六七八九十\d]+點(?:半)?",
        ]
        for pat in time_patterns:
            m = re.search(pat, text)
            if m:
                entities["time"] = m.group(0)
                break

    # Use text as title fallback if nothing else
    if "title" not in entities and "description" not in entities:
        # Strip action words to get a cleaner title
        clean = re.sub(
            r"^(?:我要|請|幫我)?(?:增加|新增|加|排|安排|約|建立?)\s*", "", text
        )
        clean = re.sub(r"(?:的行程|的會議)$", "", clean)
        if clean and clean != text:
            entities["title"] = clean


async def _action_create_reminder(text: str) -> "AssistantResponse":
    """Create a reminder."""
    from services.nexus.assistant.engine import AssistantResponse

    # Reminders are a future feature — for now acknowledge and suggest calendar
    return AssistantResponse(
        text=(
            f"⏰ 提醒功能開發中！\n\n"
            f"你的提醒：「{text}」\n"
            f"建議先用行事曆建立一個事件作為提醒。"
        ),
        intent=Intent.ACTION_CREATE_REMINDER,
        suggestions=["排一個會議作為提醒"],
    )


async def _action_update_deal(text: str) -> "AssistantResponse":
    """Update a deal field from natural language."""
    from services.nexus.assistant.engine import AssistantResponse

    # Parse what to update — future: AI-powered parsing
    return AssistantResponse(
        text=(
            "📝 更新商機功能開發中。\n\n"
            "目前可以在 Web 介面直接編輯商機資料。"
        ),
        intent=Intent.ACTION_UPDATE_DEAL,
    )


async def _action_generate_pitch(text: str) -> "AssistantResponse":
    """Generate an outreach pitch for a company."""
    from services.nexus.assistant.engine import AssistantResponse
    from services.nexus.outreach import generate_pitch, get_case_studies, get_solutions

    company = _extract_company_from_text(text)
    if not company:
        return AssistantResponse(
            text="請告訴我要為哪家公司寫說帖，例如「幫美珍香寫說帖」",
            intent=Intent.ACTION_GENERATE_PITCH,
        )

    # Find client industry
    industry = None
    try:
        from services.nexus.clients import find_client_by_name
        clients = await asyncio.to_thread(find_client_by_name, company)
        if clients:
            industry = clients[0].get("industry")
    except Exception:
        pass

    # Get matching materials
    cases = await asyncio.to_thread(get_case_studies, industry)
    solutions = await asyncio.to_thread(get_solutions, industry)

    result = await asyncio.to_thread(
        generate_pitch,
        target_company=company,
        target_industry=industry or "未知",
        case_studies=cases,
        solutions=solutions,
    )

    if result.get("error"):
        return AssistantResponse(
            text=f"⚠️ 產生說帖失敗：{result['error']}",
            intent=Intent.ACTION_GENERATE_PITCH,
        )

    return AssistantResponse(
        text=f"📝 為「{company}」產生的說帖：\n\n{result['pitch']}",
        intent=Intent.ACTION_GENERATE_PITCH,
        card_data={"type": "pitch", "company": company, "pitch": result["pitch"]},
    )
