"""Intent detection router — LLM-based classification replacing regex patterns.

Uses Claude (or active AI provider) to semantically classify user intent,
solving the fundamental brittleness of regex keyword matching.
"""

from __future__ import annotations

import asyncio
import json
import logging

from services.nexus.assistant.intents import Intent

logger = logging.getLogger(__name__)

# All valid intent names for validation
_VALID_INTENTS = {i.name for i in Intent}


async def detect_intent(
    text: str,
    input_type: str = "text",
    has_active_conversation: bool = False,
) -> tuple[Intent, dict]:
    """Detect user intent from text using LLM classification.

    Fast-path for deterministic cases (commands, photos, active sessions),
    then falls back to LLM for semantic classification.

    Returns:
        (Intent, entities) tuple where entities may contain extracted
        company, date, time, title, etc.
    """
    # 1. Active conversation — always followup
    if has_active_conversation:
        return Intent.FOLLOWUP, {}

    # 2. Photo → business card
    if input_type == "photo":
        return Intent.CAPTURE_CARD, {}

    if not text:
        return Intent.CAPTURE_GENERAL, {}

    text_stripped = text.strip()

    # 3. Slash commands
    if text_stripped.startswith("/"):
        return Intent.COMMAND, {}

    # 4. LLM classification
    return await _llm_classify(text_stripped)


async def _llm_classify(text: str) -> tuple[Intent, dict]:
    """Call LLM to classify intent and extract entities."""
    from services.ai_provider import generate_ai_response
    from services.nexus.prompts.router_classify import INTENT_CLASSIFY_PROMPT

    try:
        raw = await asyncio.to_thread(
            generate_ai_response, INTENT_CLASSIFY_PROMPT, text
        )
        result = _parse_llm_response(raw)
        intent_name = result.get("intent", "").upper()

        if intent_name not in _VALID_INTENTS:
            logger.warning("LLM returned unknown intent %r, falling back", intent_name)
            return Intent.CAPTURE_GENERAL, {}

        entities = result.get("entities", {})
        # Remove None/empty values from entities
        entities = {k: v for k, v in entities.items() if v}

        return Intent[intent_name], entities

    except Exception:
        logger.exception("LLM intent classification failed, falling back to CAPTURE_GENERAL")
        return Intent.CAPTURE_GENERAL, {}


def _parse_llm_response(raw: str) -> dict:
    """Parse JSON from LLM response, stripping markdown fences if present."""
    text = raw.strip()
    # Strip markdown code fences
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first line (```json) and last line (```)
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    return json.loads(text)
