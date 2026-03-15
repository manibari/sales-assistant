"""Settings manager — CRUD for integration configs and notification preferences."""

import json

from database.connection import get_connection, row_to_dict, rows_to_dicts


# --- Integration config ---


def get_all_integration_configs() -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM nx_integration_config ORDER BY provider"
            )
            return rows_to_dicts(cur)


def get_integration_config(provider: str) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM nx_integration_config WHERE provider = %s",
                (provider,),
            )
            return row_to_dict(cur)


def upsert_integration_config(
    provider: str, enabled: bool | None = None, config: dict | None = None
) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO nx_integration_config (provider, enabled, config_json)
                   VALUES (%s, %s, %s)
                   ON CONFLICT (provider) DO UPDATE SET
                     enabled = COALESCE(EXCLUDED.enabled, nx_integration_config.enabled),
                     config_json = COALESCE(EXCLUDED.config_json, nx_integration_config.config_json),
                     updated_at = NOW()
                   RETURNING *""",
                (provider, enabled or False, json.dumps(config or {})),
            )
            return row_to_dict(cur)


def update_integration_status(
    provider: str, status: str, error_message: str | None = None
) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE nx_integration_config
                   SET status = %s, error_message = %s, updated_at = NOW()
                   WHERE provider = %s
                   RETURNING *""",
                (status, error_message, provider),
            )
            return row_to_dict(cur)


def delete_integration_config(provider: str) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM nx_integration_config WHERE provider = %s",
                (provider,),
            )


# --- Notification preferences (stored in app_settings) ---


def get_notification_preferences() -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT value FROM app_settings WHERE key = 'notification_preferences'"
            )
            row = cur.fetchone()
            if row and row[0]:
                return json.loads(row[0])
            return {
                "email_enabled": False,
                "telegram_enabled": False,
                "frequency": "daily",
                "events": {
                    "deal_stage_change": True,
                    "meeting_reminder": True,
                    "document_expiry": True,
                    "intel_received": False,
                },
            }


def update_notification_preferences(prefs: dict) -> dict:
    value = json.dumps(prefs)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO app_settings (key, value) VALUES ('notification_preferences', %s)
                   ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value""",
                (value,),
            )
    return prefs


# --- AI provider settings ---


def get_ai_settings() -> dict:
    """Get AI provider config from integration_config table, fallback to env."""
    import os

    config = get_integration_config("ai")
    if config and config.get("config_json"):
        cfg = config["config_json"] if isinstance(config["config_json"], dict) else json.loads(config["config_json"])
        return {
            "provider": cfg.get("provider", os.getenv("AI_PROVIDER", "gemini")),
            "has_api_key": bool(cfg.get("api_key")),
            "status": config.get("status", "disconnected"),
            "enabled": config.get("enabled", False),
        }
    return {
        "provider": os.getenv("AI_PROVIDER", "gemini"),
        "has_api_key": bool(
            os.getenv("GOOGLE_API_KEY")
            or os.getenv("AZURE_OPENAI_KEY")
            or os.getenv("ANTHROPIC_API_KEY")
        ),
        "status": "env_configured",
        "enabled": True,
    }


def update_ai_settings(provider: str, api_key: str | None = None) -> dict:
    """Update AI provider settings in DB."""
    config = {"provider": provider}
    if api_key:
        from services.nexus.crypto import encrypt_value

        config["api_key"] = encrypt_value(api_key)
    return upsert_integration_config("ai", enabled=True, config=config)


def test_ai_connection(provider: str | None = None) -> dict:
    """Test connection to the AI provider."""
    import os

    target = provider or os.getenv("AI_PROVIDER", "gemini")
    try:
        if target == "gemini":
            import google.generativeai as genai

            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            model = genai.GenerativeModel("gemini-2.0-flash")
            resp = model.generate_content("Reply with exactly: OK")
            return {"success": True, "provider": target, "response": resp.text[:50]}
        elif target == "anthropic":
            import anthropic

            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            resp = client.messages.create(
                model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
                max_tokens=10,
                messages=[{"role": "user", "content": "Reply with exactly: OK"}],
            )
            return {"success": True, "provider": target, "response": resp.content[0].text[:50]}
        elif target == "azure_openai":
            from openai import AzureOpenAI

            client = AzureOpenAI(
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
                api_key=os.getenv("AZURE_OPENAI_KEY", ""),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01"),
            )
            resp = client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT", ""),
                messages=[{"role": "user", "content": "Reply with exactly: OK"}],
                max_tokens=10,
            )
            return {"success": True, "provider": target, "response": resp.choices[0].message.content[:50]}
        else:
            return {"success": False, "provider": target, "error": f"Unknown provider: {target}"}
    except Exception as e:
        return {"success": False, "provider": target, "error": str(e)}
