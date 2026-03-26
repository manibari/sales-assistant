"""Nexus Assistant Engine — unified conversational AI for Telegram and Web."""

from services.nexus.assistant.intents import Intent
from services.nexus.assistant.router import detect_intent
from services.nexus.assistant.engine import AssistantEngine, AssistantResponse, engine

__all__ = ["Intent", "detect_intent", "AssistantEngine", "AssistantResponse", "engine"]
