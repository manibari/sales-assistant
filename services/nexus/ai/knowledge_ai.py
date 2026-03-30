"""AI enhancement for knowledge chunks — summarization only.

Called by services/nexus/knowledge.py (and knowledge_worker.py) after text extraction.
"""

import json
import logging

from services.ai_provider import generate_ai_response, check_ai_available
from services.nexus.prompts import KNOWLEDGE_SUMMARIZE_PROMPT

logger = logging.getLogger(__name__)


def summarize_chunk(content: str) -> dict:
    """Use AI to generate summary and tags for a knowledge chunk.

    Returns {"summary": str | None, "tags": list[str]}.
    Falls back gracefully on failure or when AI is unavailable.
    """
    available, _ = check_ai_available()
    if not available:
        return {"summary": None, "tags": []}

    try:
        truncated = content[:3000] if len(content) > 3000 else content
        response = generate_ai_response(KNOWLEDGE_SUMMARIZE_PROMPT, truncated)

        cleaned = response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:])
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

        parsed = json.loads(cleaned)
        return {
            "summary": parsed.get("summary"),
            "tags": parsed.get("tags", []),
        }
    except Exception as e:
        logger.warning("AI summarize failed: %s", e)
        return {"summary": None, "tags": []}
