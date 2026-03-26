"""Action handlers — create deals, meetings, reminders; update deals; generate pitches.

These handlers perform write operations and return confirmation.
"""

from __future__ import annotations

import asyncio
import logging
import re

from services.nexus.assistant.intents import Intent

logger = logging.getLogger(__name__)


async def handle_action(
    engine: "AssistantEngine",
    session_id: str,
    text: str,
    intent: Intent,
) -> "AssistantResponse":
    """Route to the appropriate action handler."""
    from services.nexus.assistant.engine import AssistantResponse

    match intent:
        case Intent.ACTION_CREATE_DEAL:
            return await _action_create_deal(text)
        case Intent.ACTION_CREATE_MEETING:
            return await _action_create_meeting(text)
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


async def _action_create_meeting(text: str) -> "AssistantResponse":
    """Create a meeting from natural language."""
    from services.nexus.assistant.engine import AssistantResponse

    try:
        from services.nexus.calendar import create_meeting

        # Extract date/time and company from text
        company = _extract_company_from_text(text)

        # Try to find client
        client_id = None
        client_name = company or ""
        if company:
            from services.nexus.clients import find_client_by_name
            clients = await asyncio.to_thread(find_client_by_name, company)
            if clients:
                client_id = clients[0]["id"]
                client_name = clients[0]["name"]

        # For now, create a basic meeting with the text as title
        meeting = await asyncio.to_thread(
            create_meeting,
            title=text,
            client_id=client_id,
        )

        return AssistantResponse(
            text=(
                f"📅 已建立會議\n"
                f"標題：{text}\n"
                + (f"客戶：{client_name}\n" if client_name else "")
                + "\n可以在行事曆中編輯詳細時間和地點"
            ),
            intent=Intent.ACTION_CREATE_MEETING,
            actions_taken=[{"type": "create_meeting", "id": meeting.get("id")}],
        )
    except ImportError:
        return AssistantResponse(
            text="📅 行事曆模組尚未啟用，暫時無法排會議。",
            intent=Intent.ACTION_CREATE_MEETING,
        )
    except Exception as e:
        logger.error("Create meeting failed: %s", e)
        return AssistantResponse(
            text=f"⚠️ 建立會議失敗：{e}",
            intent=Intent.ACTION_CREATE_MEETING,
        )


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
