"""Shared role definitions and format conventions for all prompts."""

# Common role prefix for B2B sales assistant context
SALES_ASSISTANT_ROLE = "You are a helpful B2B sales assistant."

# Common system instruction for Traditional Chinese replies
REPLY_ZH_TW = "Reply in Traditional Chinese (繁體中文)."

# JSON output instruction (reused across parse prompts)
JSON_ONLY_INSTRUCTION = (
    "Return ONLY a JSON object. Do NOT wrap in markdown code fences.\n"
    "Omit any field you are not confident about — never guess."
)
