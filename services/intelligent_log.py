"""Service for handling AI-powered parsing of natural language log entries.

This service will interact with the Gemini API to extract structured data
from unstructured text.
"""

import os
import json
import google.generativeai as genai

# Configure the Gemini API key
# The user must have GOOGLE_API_KEY set in their .env file
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# System prompt to instruct the Gemini model
_SYSTEM_PROMPT = """
You are an expert assistant for a B2B Sales & Project Management System (SPMS).
Your task is to parse a user's natural language work log entry and extract structured information.
The user will provide a text entry. You MUST return a single JSON object with the following schema.
Do not return any other text, just the JSON object.

Schema:
{
  "company_name": "string or null",  // The name of the client company mentioned.
  "log_content": "string",             // The full, original text from the user.
  "action_type": "string"              // Infer the type of activity from the text. Choose one of: "會議", "提案", "開發", "文件", "郵件". Default to "會議".
}

Example user input:
"今天拜訪桃園大眾捷運股份有限公司，討論關於車上冰水主機、轉轍器等議題"

Example JSON output:
{
  "company_name": "桃園大眾捷運股份有限公司",
  "log_content": "今天拜訪桃園大眾捷運股份有限公司，討論關於車上冰水主機、轉轍器等議題",
  "action_type": "會議"
}
"""

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

    try:
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=_SYSTEM_PROMPT
        )
        response = model.generate_content(text_input)

        # Clean the response to get only the JSON part
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
        parsed_json = json.loads(cleaned_response)

        # Ensure the original text is preserved as log_content
        parsed_json['log_content'] = text_input
        return parsed_json

    except Exception as e:
        print(f"Error parsing log entry with Gemini: {e}")
        return None
