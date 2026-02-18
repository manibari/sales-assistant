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

def parse_log_entry(text_input: str) -> dict | None:
    """
    Parses a natural language log entry using the configured AI provider.

    Args:
        text_input: The user's unstructured text log.

    Returns:
        A dictionary with the structured data, or None if parsing fails.
    """
    available, msg = check_ai_available()
    if not available:
        raise ValueError(msg)

    if not text_input or not text_input.strip():
        return None

    system_prompt = get_ai_prompt()
    if not system_prompt:
        raise ValueError("System prompt for 'ai_smart_log' could not be loaded from prompts.yml.")

    raw_response_text = ""
    try:
        raw_response_text = generate_ai_response(system_prompt, text_input)

        # Clean the response to get only the JSON part
        cleaned_response = raw_response_text.replace("```json", "").replace("```", "")
        parsed_json = json.loads(cleaned_response)

        # Ensure the original text is preserved as log_content
        parsed_json['log_content'] = text_input
        return parsed_json

    except json.JSONDecodeError as e:
        logger.error(
            "AI response parsing failed. Error: %s\nRaw response:\n%s",
            e, raw_response_text,
        )
        return None
    except Exception as e:
        logger.exception("Unexpected error in parse_log_entry: %s", e)
        return None
