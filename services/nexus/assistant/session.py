"""Session manager — manages multi-turn conversation state and conversation memory.

Replaces the _conversations dict from telegram.py with a structured
manager that can be shared between Telegram and Web adapters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.nexus.assistant.intents import Intent


# ---------------------------------------------------------------------------
# Conversation memory — persists across task sessions
# ---------------------------------------------------------------------------

# Maximum messages to keep in conversation memory per user
_MAX_MEMORY_MESSAGES = 20


@dataclass
class MemoryEntry:
    """A single message in conversation memory."""

    role: str  # "user" or "assistant"
    text: str
    intent: str | None = None
    entities: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ConversationMemory:
    """Rolling conversation memory per session — survives across task sessions.

    Stores recent user/assistant messages with extracted entities,
    enabling context-aware intent detection and pronoun resolution.
    """

    def __init__(self, max_messages: int = _MAX_MEMORY_MESSAGES) -> None:
        self._histories: dict[str, list[MemoryEntry]] = {}
        self._max = max_messages

    def add(
        self,
        session_id: str,
        role: str,
        text: str,
        intent: str | None = None,
        entities: dict | None = None,
    ) -> None:
        """Record a message into conversation memory."""
        if not text:
            return
        history = self._histories.setdefault(session_id, [])
        history.append(MemoryEntry(
            role=role,
            text=text,
            intent=intent,
            entities=entities or {},
        ))
        # Trim to max
        if len(history) > self._max:
            self._histories[session_id] = history[-self._max:]

    def get_recent(self, session_id: str, n: int = 10) -> list[MemoryEntry]:
        """Get the last N messages for a session."""
        history = self._histories.get(session_id, [])
        return history[-n:]

    def get_recent_entities(self, session_id: str, n: int = 10) -> dict:
        """Merge entities from the last N messages (most recent wins)."""
        merged: dict = {}
        for entry in self.get_recent(session_id, n):
            for k, v in entry.entities.items():
                if v:
                    merged[k] = v
        return merged

    def format_context(self, session_id: str, n: int = 6) -> str:
        """Format recent conversation as context string for LLM prompts."""
        recent = self.get_recent(session_id, n)
        if not recent:
            return ""
        lines = []
        for entry in recent:
            role_label = "使用者" if entry.role == "user" else "助理"
            lines.append(f"{role_label}: {entry.text}")
        return "\n".join(lines)

    def clear(self, session_id: str) -> None:
        """Clear all memory for a session."""
        self._histories.pop(session_id, None)


# ---------------------------------------------------------------------------
# Task session — active multi-turn task state
# ---------------------------------------------------------------------------


@dataclass
class Session:
    """Active conversation session."""

    session_id: str
    intel_id: int | None = None
    intent: Intent | None = None
    parsed: dict = field(default_factory=dict)
    card_base: dict = field(default_factory=dict)
    chat_history: list[dict] = field(default_factory=list)
    raw_history: list[str] = field(default_factory=list)
    input_type: str = "text"
    pending_industry_confirm: bool = False
    pending_role_confirm: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_active(self) -> bool:
        return self.intel_id is not None

    def merge_fields(self, new_fields: dict) -> None:
        """Merge new parsed fields into session, preserving card_base."""
        for k, v in new_fields.items():
            if v is not None:
                self.parsed[k] = v
        # Re-merge card_base so OCR fields are never lost
        for k, v in self.card_base.items():
            if k not in self.parsed:
                self.parsed[k] = v


class SessionManager:
    """In-memory session store — thread-safe for asyncio (single-threaded event loop)."""

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def get_or_create(self, session_id: str) -> Session:
        if session_id not in self._sessions:
            self._sessions[session_id] = Session(session_id=session_id)
        return self._sessions[session_id]

    def create(self, session_id: str, **kwargs) -> Session:
        """Create a new session, replacing any existing one."""
        session = Session(session_id=session_id, **kwargs)
        self._sessions[session_id] = session
        return session

    def close(self, session_id: str) -> Session | None:
        """Remove and return the session."""
        return self._sessions.pop(session_id, None)

    def has_active(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        return session is not None and session.is_active

    def list_active(self) -> list[str]:
        return [sid for sid, s in self._sessions.items() if s.is_active]
