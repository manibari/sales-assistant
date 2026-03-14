"""Service for handling AI-powered parsing of natural language log entries.

This service interacts with the configured AI provider to extract structured
data from unstructured text.
"""

import json
import logging

from services.ai_provider import check_ai_available, generate_ai_response
from services.config import get_ai_prompt

logger = logging.getLogger(__name__)

# --- AI Log Parsing ---


def parse_log_entry(text_input: str) -> list[dict] | None:
    """
    Parses a natural language log entry using the configured AI provider.

    Args:
        text_input: The user's unstructured text log (single or batch).

    Returns:
        A list of dicts with the structured data, or None if parsing fails.
        Always returns a list (even for single entries) for uniform handling.
    """
    available, msg = check_ai_available()
    if not available:
        raise ValueError(msg)

    if not text_input or not text_input.strip():
        return None

    system_prompt = get_ai_prompt()
    if not system_prompt:
        raise ValueError(
            "System prompt for 'ai_smart_log' could not be loaded from prompts.yml."
        )

    raw_response_text = ""
    try:
        raw_response_text = generate_ai_response(system_prompt, text_input)

        # Clean the response to get only the JSON part
        cleaned_response = raw_response_text.replace("```json", "").replace("```", "")
        parsed_json = json.loads(cleaned_response)

        # Defensive: AI might return a single dict instead of a list
        if isinstance(parsed_json, dict):
            parsed_json = [parsed_json]

        if not isinstance(parsed_json, list) or not parsed_json:
            return None

        # For single-entry input, preserve the original text as log_content
        if len(parsed_json) == 1:
            parsed_json[0]["log_content"] = text_input

        return parsed_json

    except json.JSONDecodeError as e:
        logger.error(
            "AI response parsing failed. Error: %s\nRaw response:\n%s",
            e,
            raw_response_text,
        )
        return None
    except Exception as e:
        logger.exception("Unexpected error in parse_log_entry: %s", e)
        return None
