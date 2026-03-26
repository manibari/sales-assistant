"""Unified Assistant Engine — core conversation logic for Telegram and Web.

All conversation flow lives here. Transport adapters (Telegram webhook, Web API)
call engine.handle_message() and format the response for their channel.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from services.nexus.assistant.intents import Intent
from services.nexus.assistant.router import detect_intent
from services.nexus.assistant.session import ConversationMemory, Session, SessionManager

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Response model
# ---------------------------------------------------------------------------


@dataclass
class AssistantResponse:
    """Structured response from the engine — adapters render this per-channel."""

    text: str
    intent: Intent
    parsed_update: dict | None = None
    actions_taken: list[dict] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    card_data: dict | None = None  # structured card for web UI rendering
    intel_id: int | None = None
    session_closed: bool = False


# ---------------------------------------------------------------------------
# Pending deal state (per session)
# ---------------------------------------------------------------------------

# { session_id: { "intel_id", "client_id", "client_name", "parsed" } }
_pending_deal: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Engine singleton
# ---------------------------------------------------------------------------


class AssistantEngine:
    """Unified assistant engine — Telegram and Web both call here."""

    def __init__(self) -> None:
        self.sessions = SessionManager()
        self.memory = ConversationMemory()

    async def handle_message(
        self,
        session_id: str,
        text: str,
        input_type: str = "text",
        image_bytes: bytes | None = None,
    ) -> AssistantResponse:
        """Main entry point — detect intent, route to handler, return response."""
        has_active = self.sessions.has_active(session_id)

        # Build conversation context for LLM router
        conversation_context = self.memory.format_context(session_id)

        # Detect intent (async — may call LLM)
        intent, entities = await detect_intent(
            text=text,
            input_type=input_type,
            has_active_conversation=has_active,
            conversation_context=conversation_context,
        )

        # Record user message to conversation memory
        self.memory.add(
            session_id, "user", text,
            intent=intent.name, entities=entities,
        )

        # Check for pending deal response first
        if session_id in _pending_deal and text:
            result = await self._handle_deal_response(session_id, text)
            if result is not None:
                return result
            # Not a yes/no → clear pending, fall through
            _pending_deal.pop(session_id, None)

        # Route by intent category
        match intent:
            case Intent.COMMAND:
                response = await self.handle_command(session_id, text)

            case Intent.FOLLOWUP:
                response = await self._handle_followup(session_id, text)

            case intent if intent.category == "capture":
                response = await self._handle_capture(
                    session_id, text, intent, input_type, image_bytes
                )

            case intent if intent.category == "query":
                response = await self._handle_query(session_id, text, intent)

            case intent if intent.category == "action":
                response = await self._handle_action(
                    session_id, text, intent, entities
                )

            case _:
                response = AssistantResponse(
                    text="⚠️ 無法理解你的訊息，請重新輸入",
                    intent=intent,
                )

        # Record assistant response to conversation memory
        self.memory.add(session_id, "assistant", response.text, intent=intent.name)
        return response

    # ------------------------------------------------------------------
    # Capture handler (intel input)
    # ------------------------------------------------------------------

    async def _handle_capture(
        self,
        session_id: str,
        text: str,
        intent: Intent,
        input_type: str,
        image_bytes: bytes | None = None,
    ) -> AssistantResponse:
        from services.nexus.assistant.handlers.capture import handle_capture

        return await handle_capture(
            engine=self,
            session_id=session_id,
            text=text,
            intent=intent,
            input_type=input_type,
            image_bytes=image_bytes,
        )

    async def _handle_followup(
        self, session_id: str, text: str
    ) -> AssistantResponse:
        # Check if the active session is an action (e.g. multi-turn meeting creation)
        session = self.sessions.get(session_id)
        if session and session.intent and session.intent.category == "action":
            from services.nexus.assistant.handlers.action import handle_action
            return await handle_action(
                engine=self, session_id=session_id, text=text,
                intent=session.intent, entities={},
            )

        from services.nexus.assistant.handlers.capture import handle_followup
        return await handle_followup(engine=self, session_id=session_id, text=text)

    # ------------------------------------------------------------------
    # Command handler
    # ------------------------------------------------------------------

    async def handle_command(
        self, session_id: str, command: str
    ) -> AssistantResponse:
        """Handle /done, /cancel, /status, /today, /new."""
        cmd = command.strip().split()[0].lower()

        if cmd in ("/done", "/確認"):
            from services.nexus.assistant.handlers.capture import handle_done
            return await handle_done(engine=self, session_id=session_id)

        if cmd in ("/cancel", "/取消"):
            session = self.sessions.close(session_id)
            if not session:
                return AssistantResponse(
                    text="目前沒有進行中的情報",
                    intent=Intent.COMMAND,
                )
            # Action sessions (e.g. meeting creation) use intel_id=-1
            if session.intent and session.intent.category == "action":
                return AssistantResponse(
                    text="已取消操作。",
                    intent=Intent.COMMAND,
                    session_closed=True,
                )
            return AssistantResponse(
                text=f"已取消。情報 #{session.intel_id} 保留為草稿",
                intent=Intent.COMMAND,
                session_closed=True,
            )

        if cmd in ("/status", "/狀態"):
            from services.nexus.assistant.handlers.capture import handle_status
            return await handle_status(engine=self, session_id=session_id)

        if cmd in ("/today", "/待辦"):
            from services.nexus.assistant.handlers.query import handle_today
            return await handle_today()

        if cmd == "/new":
            self.sessions.close(session_id)
            _pending_deal.pop(session_id, None)
            return AssistantResponse(
                text="好的，傳訊息開始新的情報！",
                intent=Intent.COMMAND,
            )

        if cmd == "/start":
            return AssistantResponse(
                text=(
                    "👋 你好！我是你的情報助理。\n\n"
                    "直接傳訊息、照片或檔案給我，我會幫你建立情報並自動分類。\n\n"
                    "你也可以：\n"
                    "• 查詢：「查 美珍香」「最近有什麼標案」「今天行程」\n"
                    "• 行動：「幫美珍香建案子」「排下週三開會」\n\n"
                    "指令：\n"
                    "/done — 確認並儲存情報\n"
                    "/cancel — 取消目前情報\n"
                    "/status — 查看目前進度\n"
                    "/new — 強制開始新情報\n"
                    "/today — 今日待辦摘要"
                ),
                intent=Intent.COMMAND,
            )

        return AssistantResponse(
            text="未知指令。可用：/done /cancel /status /new /today",
            intent=Intent.COMMAND,
        )

    # ------------------------------------------------------------------
    # Query handler
    # ------------------------------------------------------------------

    async def _handle_query(
        self, session_id: str, text: str, intent: Intent
    ) -> AssistantResponse:
        from services.nexus.assistant.handlers.query import handle_query

        return await handle_query(text=text, intent=intent)

    # ------------------------------------------------------------------
    # Action handler
    # ------------------------------------------------------------------

    async def _handle_action(
        self, session_id: str, text: str, intent: Intent,
        entities: dict | None = None,
    ) -> AssistantResponse:
        from services.nexus.assistant.handlers.action import handle_action

        return await handle_action(
            engine=self, session_id=session_id, text=text, intent=intent,
            entities=entities or {},
        )

    # ------------------------------------------------------------------
    # Deal response handler
    # ------------------------------------------------------------------

    async def _handle_deal_response(
        self, session_id: str, text: str
    ) -> AssistantResponse | None:
        """Handle yes/no response to deal creation prompt."""
        pending = _pending_deal.get(session_id)
        if not pending:
            return None

        low = text.lower().strip()
        if low in ("是", "yes", "ok", "好", "建立", "對"):
            from services.nexus.assistant.handlers.capture import auto_create_deal

            result = await auto_create_deal(
                intel_id=pending["intel_id"],
                client_id=pending["client_id"],
                client_name=pending["client_name"],
                parsed=pending["parsed"],
            )
            _pending_deal.pop(session_id, None)
            if result:
                return AssistantResponse(
                    text=(
                        f"💼 已建立商機「{result['name']}」(#{result['id']})\n"
                        f"階段：L0 | 客戶：{pending['client_name']}\n\n"
                        f"傳新訊息可開始下一筆情報"
                    ),
                    intent=Intent.FOLLOWUP,
                    actions_taken=[{"type": "create_deal", **result}],
                )
            return AssistantResponse(
                text="⚠️ 建立商機失敗，請稍後重試\n傳新訊息可開始下一筆情報",
                intent=Intent.FOLLOWUP,
            )

        if low in ("否", "no", "不", "不用", "跳過", "skip"):
            _pending_deal.pop(session_id, None)
            return AssistantResponse(
                text="好的，跳過建立商機。\n傳新訊息可開始下一筆情報",
                intent=Intent.FOLLOWUP,
            )

        # Not a yes/no — return None to let caller handle as new intel
        return None


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

engine = AssistantEngine()
