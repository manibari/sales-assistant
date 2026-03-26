"""Web chat API — thin adapter over the unified Assistant Engine.

Provides REST endpoints for the web frontend to interact with the assistant.
"""

import logging
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from services.nexus.assistant.engine import engine, AssistantResponse

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str
    text: str
    input_type: str = "text"


class ChatResponse(BaseModel):
    text: str
    intent: str
    intent_category: str
    parsed_update: dict | None = None
    actions_taken: list[dict] = []
    suggestions: list[str] = []
    card_data: dict | None = None
    intel_id: int | None = None
    session_closed: bool = False


class CommandRequest(BaseModel):
    session_id: str
    command: str


@router.post("/chat", response_model=ChatResponse)
async def assistant_chat(body: ChatRequest):
    """Process a chat message through the assistant engine."""
    response = await engine.handle_message(
        session_id=body.session_id,
        text=body.text,
        input_type=body.input_type,
    )
    return _to_chat_response(response)


@router.post("/command", response_model=ChatResponse)
async def assistant_command(body: CommandRequest):
    """Process a slash command through the assistant engine."""
    response = await engine.handle_command(
        session_id=body.session_id,
        command=body.command,
    )
    return _to_chat_response(response)


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get current session state (for UI sync)."""
    session = engine.sessions.get(session_id)
    if not session:
        return {"active": False}
    return {
        "active": session.is_active,
        "intel_id": session.intel_id,
        "intent": session.intent.value if session.intent else None,
        "parsed": session.parsed,
        "input_type": session.input_type,
        "pending_role_confirm": session.pending_role_confirm,
        "pending_industry_confirm": session.pending_industry_confirm,
        "message_count": len(session.chat_history),
    }


@router.get("/sessions")
async def list_sessions():
    """List active sessions (admin/debug)."""
    return {"active_sessions": engine.sessions.list_active()}


def _to_chat_response(response: AssistantResponse) -> ChatResponse:
    """Convert engine response to API response model."""
    return ChatResponse(
        text=response.text,
        intent=response.intent.value,
        intent_category=response.intent.category,
        parsed_update=response.parsed_update,
        actions_taken=response.actions_taken,
        suggestions=response.suggestions,
        card_data=response.card_data,
        intel_id=response.intel_id,
        session_closed=response.session_closed,
    )
