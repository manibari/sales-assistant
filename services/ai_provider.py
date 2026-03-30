"""Multi-provider AI dispatcher.

Supports Google Gemini, Azure OpenAI, and Anthropic Claude.
Provider is selected via the AI_PROVIDER env var (default: "gemini").
SDKs are lazy-imported so only the active provider's SDK is required.
"""

import logging
import os

logger = logging.getLogger(__name__)

_VALID_PROVIDERS = ("gemini", "azure_openai", "anthropic")


def get_provider_name() -> str:
    """Return the active AI provider name from AI_PROVIDER env var."""
    return os.getenv("AI_PROVIDER", "gemini").lower().strip()


def check_ai_available() -> tuple[bool, str]:
    """Check whether the active provider's required env vars are set.

    Returns:
        (True, provider_name) if ready, or (False, error_message) if not.
    """
    provider = get_provider_name()

    if provider not in _VALID_PROVIDERS:
        return False, (
            f'AI_PROVIDER="{provider}" 不是有效的選項。'
            f"請設定為：{', '.join(_VALID_PROVIDERS)}"
        )

    if provider == "gemini":
        if not os.getenv("GOOGLE_API_KEY"):
            return False, "請在 .env 設定 GOOGLE_API_KEY 以啟用 Google Gemini。"
        return True, provider

    if provider == "azure_openai":
        missing = [
            v
            for v in (
                "AZURE_OPENAI_ENDPOINT",
                "AZURE_OPENAI_KEY",
                "AZURE_OPENAI_DEPLOYMENT",
            )
            if not os.getenv(v)
        ]
        if missing:
            return False, f"Azure OpenAI 缺少環境變數：{', '.join(missing)}"
        return True, provider

    # anthropic
    if not os.getenv("ANTHROPIC_API_KEY"):
        return False, "請在 .env 設定 ANTHROPIC_API_KEY 以啟用 Anthropic Claude。"
    return True, provider


def generate_ai_vision_response(
    system_prompt: str,
    user_text: str,
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
) -> str:
    """Dispatch a vision AI call (text + image) to the active provider.

    Args:
        system_prompt: The system instruction / prompt.
        user_text: The user's input text (can be empty).
        image_bytes: Raw image bytes.
        mime_type: MIME type of the image.

    Returns:
        The raw text response from the AI model.
    """
    provider = get_provider_name()

    if provider == "gemini":
        return _call_gemini_vision(system_prompt, user_text, image_bytes, mime_type)
    if provider == "azure_openai":
        return _call_azure_openai_vision(
            system_prompt, user_text, image_bytes, mime_type
        )
    if provider == "anthropic":
        return _call_anthropic_vision(system_prompt, user_text, image_bytes, mime_type)

    raise ValueError(f"Unknown AI_PROVIDER: {provider}")


def generate_ai_response(system_prompt: str, user_text: str) -> str:
    """Dispatch an AI call to the active provider.

    Args:
        system_prompt: The system instruction / prompt.
        user_text: The user's input text.

    Returns:
        The raw text response from the AI model.

    Raises:
        ValueError: If provider config is invalid or missing.
        RuntimeError: If the SDK call fails.
    """
    provider = get_provider_name()

    if provider == "gemini":
        return _call_gemini(system_prompt, user_text)
    if provider == "azure_openai":
        return _call_azure_openai(system_prompt, user_text)
    if provider == "anthropic":
        return _call_anthropic(system_prompt, user_text)

    raise ValueError(f"Unknown AI_PROVIDER: {provider}")


def generate_embedding(text: str) -> list[float]:
    """Generate text embedding using Google text-embedding-004.

    Always uses Google/Gemini regardless of AI_PROVIDER env var.
    Requires GOOGLE_API_KEY to be set.
    """
    import google.generativeai as genai  # noqa: E402 — lazy import

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not set — cannot generate embeddings")
    genai.configure(api_key=api_key)
    result = genai.embed_content(model="models/text-embedding-004", content=text)
    return result["embedding"]


def generate_ai_with_tools(
    system_prompt: str,
    messages: list[dict],
    tools: list[dict],
    provider: str | None = None,
) -> dict:
    """Tool-calling AI dispatch. Uses AGENT_PROVIDER env var (default: gemini).

    Args:
        system_prompt: System instruction.
        messages: List of {"role": "user"|"assistant", "content": str}.
        tools: List of tool definitions (OpenAI-style function schema).
        provider: Override AGENT_PROVIDER env var.

    Returns:
        {"content": str | None, "tool_calls": [{"name": str, "arguments": dict}]}
    """
    p = provider or os.getenv("AGENT_PROVIDER", "gemini")
    if p == "gemini":
        return _call_gemini_with_tools(system_prompt, messages, tools)
    if p == "azure_openai":
        return _call_azure_openai_with_tools(system_prompt, messages, tools)
    raise ValueError(f"Tool calling not supported for provider: {p}")


def generate_ai_chat(
    system_prompt: str,
    messages: list[dict[str, str]],
) -> str:
    """Dispatch a multi-turn chat to the active provider.

    Args:
        system_prompt: The system instruction.
        messages: List of {"role": "user"|"assistant", "content": str}.

    Returns:
        The raw text response from the AI model.
    """
    provider = get_provider_name()

    if provider == "gemini":
        return _call_gemini_chat(system_prompt, messages)
    if provider == "azure_openai":
        return _call_azure_openai_chat(system_prompt, messages)
    if provider == "anthropic":
        return _call_anthropic_chat(system_prompt, messages)

    raise ValueError(f"Unknown AI_PROVIDER: {provider}")


# ---------------------------------------------------------------------------
# Private provider implementations
# ---------------------------------------------------------------------------


def _call_gemini(system_prompt: str, user_text: str) -> str:
    import google.generativeai as genai  # noqa: E402 — lazy import

    model_name = os.getenv("GOOGLE_MODEL", "gemini-2.5-flash")
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_prompt,
    )
    response = model.generate_content(user_text)
    return response.text.strip()


def _call_azure_openai(system_prompt: str, user_text: str) -> str:
    from openai import AzureOpenAI  # noqa: E402 — lazy import

    client = AzureOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_KEY"],
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01"),
    )
    response = client.chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
    )
    return response.choices[0].message.content.strip()


def _call_anthropic(system_prompt: str, user_text: str) -> str:
    import anthropic  # noqa: E402 — lazy import

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    model_name = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    response = client.messages.create(
        model=model_name,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_text}],
    )
    return response.content[0].text.strip()


# ---------------------------------------------------------------------------
# Multi-turn chat provider implementations
# ---------------------------------------------------------------------------


def _call_gemini_chat(system_prompt: str, messages: list[dict[str, str]]) -> str:
    import google.generativeai as genai  # noqa: E402

    model_name = os.getenv("GOOGLE_MODEL", "gemini-2.5-flash")
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_prompt,
    )
    # Convert to Gemini's content format
    history = []
    for msg in messages[:-1]:
        role = "user" if msg["role"] == "user" else "model"
        history.append({"role": role, "parts": [msg["content"]]})
    chat = model.start_chat(history=history)
    last_msg = messages[-1]["content"] if messages else ""
    response = chat.send_message(last_msg)
    return response.text.strip()


def _call_azure_openai_chat(
    system_prompt: str, messages: list[dict[str, str]]
) -> str:
    from openai import AzureOpenAI  # noqa: E402

    client = AzureOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_KEY"],
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01"),
    )
    api_messages = [{"role": "system", "content": system_prompt}]
    for msg in messages:
        api_messages.append({"role": msg["role"], "content": msg["content"]})
    response = client.chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        messages=api_messages,
    )
    return response.choices[0].message.content.strip()


def _call_anthropic_chat(
    system_prompt: str, messages: list[dict[str, str]]
) -> str:
    import anthropic  # noqa: E402

    client = anthropic.Anthropic()
    model_name = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    api_messages = [{"role": m["role"], "content": m["content"]} for m in messages]
    response = client.messages.create(
        model=model_name,
        max_tokens=4096,
        system=system_prompt,
        messages=api_messages,
    )
    return response.content[0].text.strip()


# ---------------------------------------------------------------------------
# Vision provider implementations
# ---------------------------------------------------------------------------


def _call_gemini_vision(
    system_prompt: str, user_text: str, image_bytes: bytes, mime_type: str
) -> str:
    import google.generativeai as genai  # noqa: E402

    model_name = os.getenv("GOOGLE_MODEL", "gemini-2.5-flash")
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_prompt,
    )
    image_part = {"mime_type": mime_type, "data": image_bytes}
    parts = [image_part]
    if user_text:
        parts.append(user_text)
    response = model.generate_content(parts)
    return response.text.strip()


def _call_azure_openai_vision(
    system_prompt: str, user_text: str, image_bytes: bytes, mime_type: str
) -> str:
    import base64
    from openai import AzureOpenAI  # noqa: E402

    client = AzureOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_KEY"],
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01"),
    )
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    data_url = f"data:{mime_type};base64,{b64}"
    user_content = [
        {"type": "image_url", "image_url": {"url": data_url}},
    ]
    if user_text:
        user_content.insert(0, {"type": "text", "text": user_text})
    response = client.chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    )
    return response.choices[0].message.content.strip()


def _call_anthropic_vision(
    system_prompt: str, user_text: str, image_bytes: bytes, mime_type: str
) -> str:
    import base64
    import anthropic  # noqa: E402

    client = anthropic.Anthropic()
    model_name = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    content = [
        {
            "type": "image",
            "source": {"type": "base64", "media_type": mime_type, "data": b64},
        },
    ]
    if user_text:
        content.append({"type": "text", "text": user_text})
    response = client.messages.create(
        model=model_name,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": content}],
    )
    return response.content[0].text.strip()


# ---------------------------------------------------------------------------
# Tool-calling provider implementations
# ---------------------------------------------------------------------------


def _call_gemini_with_tools(
    system_prompt: str,
    messages: list[dict],
    tools: list[dict],
) -> dict:
    """Gemini function-calling via google-generativeai SDK."""
    import google.generativeai as genai  # noqa: E402
    from google.generativeai.types import FunctionDeclaration, Tool  # noqa: E402

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not set")
    genai.configure(api_key=api_key)

    # Convert OpenAI-style tool defs to Gemini FunctionDeclarations
    decls = []
    for t in tools:
        fn = t.get("function", t)
        params = fn.get("parameters", {})
        decls.append(
            FunctionDeclaration(
                name=fn["name"],
                description=fn.get("description", ""),
                parameters=params,
            )
        )
    gemini_tools = [Tool(function_declarations=decls)] if decls else []

    model_name = os.getenv("GOOGLE_AGENT_MODEL", "gemini-1.5-flash")
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_prompt,
        tools=gemini_tools,
    )

    # Build history
    history = []
    for msg in messages[:-1]:
        role = "user" if msg["role"] == "user" else "model"
        history.append({"role": role, "parts": [msg["content"]]})

    chat = model.start_chat(history=history)
    last = messages[-1]["content"] if messages else ""
    response = chat.send_message(last)

    # Parse response
    tool_calls = []
    text_content = None
    for part in response.parts:
        if hasattr(part, "function_call") and part.function_call.name:
            fc = part.function_call
            tool_calls.append(
                {
                    "name": fc.name,
                    "arguments": dict(fc.args),
                }
            )
        elif hasattr(part, "text") and part.text:
            text_content = part.text.strip()

    return {"content": text_content, "tool_calls": tool_calls}


def _call_azure_openai_with_tools(
    system_prompt: str,
    messages: list[dict],
    tools: list[dict],
) -> dict:
    """Azure OpenAI function-calling."""
    from openai import AzureOpenAI  # noqa: E402

    client = AzureOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_KEY"],
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01"),
    )
    api_messages = [{"role": "system", "content": system_prompt}]
    for msg in messages:
        api_messages.append({"role": msg["role"], "content": msg["content"]})

    # Convert tool defs to OpenAI format (already compatible)
    response = client.chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        messages=api_messages,
        tools=[{"type": "function", "function": t.get("function", t)} for t in tools],
        tool_choice="auto",
    )
    msg = response.choices[0].message
    tool_calls = []
    if msg.tool_calls:
        import json as _json

        for tc in msg.tool_calls:
            tool_calls.append(
                {
                    "name": tc.function.name,
                    "arguments": _json.loads(tc.function.arguments),
                }
            )
    return {
        "content": msg.content.strip() if msg.content else None,
        "tool_calls": tool_calls,
    }
