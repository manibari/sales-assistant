"""Service for handling AI-powered parsing of natural language log entries.

This service will interact with the Gemini API to extract structured data
from unstructured text.
"""
import os
import json
import google.generativeai as genai
from services.config import get_ai_prompt

# --- Gemini API Call ---

def parse_log_entry(text_input: str) -> dict | None:
    """
    Parses a natural language log entry using the Gemini API.

    Args:
        text_input: The user's unstructured text log.

    Returns:
        A dictionary with the structured data, or None if parsing fails.
    """
    if not os.getenv("GOOGLE_API_KEY"):
        raise ValueError("GOOGLE_API_KEY environment variable not set.")

    if not text_input or not text_input.strip():
        return None

    system_prompt = get_ai_prompt()
    if not system_prompt:
        raise ValueError("System prompt for 'ai_smart_log' could not be loaded from prompts.yml.")

    raw_response_text = ""
    try:
        model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            system_instruction=system_prompt
        )
        response = model.generate_content(text_input)
        raw_response_text = response.text.strip()

        # Clean the response to get only the JSON part
        cleaned_response = raw_response_text.replace("```json", "").replace("```", "")
        parsed_json = json.loads(cleaned_response)

        # Ensure the original text is preserved as log_content
        parsed_json['log_content'] = text_input
        return parsed_json

    except json.JSONDecodeError as e:
        print("="*50)
        print("AI RESPONSE PARSING FAILED!")
        print(f"Failed to decode JSON. Error: {e}")
        print("Raw response from AI model:")
        print(raw_response_text)
        print("="*50)
        return None
    except Exception as e:
        print(f"An unexpected error occurred in parse_log_entry: {e}")
        return None

