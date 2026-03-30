"""AI enhancement for intel records — parse, summarize, chat.

Called by backend/routers/nexus/intel.py.
DB operations and chat history management stay in the router.
"""

import json
import logging

from services.ai_provider import generate_ai_response, generate_ai_chat
from services.nexus.prompts import INTEL_PARSE_PROMPT, INTEL_SUMMARIZE_PROMPT

logger = logging.getLogger(__name__)


def parse_raw_intel(raw_text: str) -> dict:
    """Parse raw intel text via AI → structured dict.

    Returns parsed dict on success, empty dict on parse failure.
    """
    ai_raw = generate_ai_response(INTEL_PARSE_PROMPT, raw_text)
    try:
        cleaned = ai_raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(cleaned)
    except (json.JSONDecodeError, IndexError):
        logger.warning("Intel parse JSON decode failed: %s", ai_raw[:200])
        return {}


def summarize_intel_records(user_prompt: str) -> str:
    """Summarize one or more intel records via AI.

    Args:
        user_prompt: Pre-composed text containing all intel sections.

    Returns:
        Summary string from AI.
    """
    return generate_ai_response(INTEL_SUMMARIZE_PROMPT, user_prompt)


def chat_intel(system_prompt: str, messages: list[dict]) -> str:
    """Multi-turn intel chat.

    Args:
        system_prompt: System instruction (FOLLOWUP_PROMPT + optional context).
        messages: List of {"role": "user"|"assistant", "content": str}.

    Returns:
        Raw AI response string.
    """
    return generate_ai_chat(system_prompt, messages)
