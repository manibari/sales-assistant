"""Settings router — integration configs, AI provider, notification preferences."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.nexus.settings_mgr import (
    get_all_integration_configs,
    get_integration_config,
    upsert_integration_config,
    delete_integration_config,
    get_notification_preferences,
    update_notification_preferences,
    get_ai_settings,
    update_ai_settings,
    test_ai_connection,
)

router = APIRouter()


# --- Pydantic models ---


class IntegrationConfigUpdate(BaseModel):
    enabled: bool | None = None
    config_json: dict | None = None


class NotificationPrefsUpdate(BaseModel):
    email_enabled: bool | None = None
    telegram_enabled: bool | None = None
    frequency: str | None = None
    events: dict | None = None


class AISettingsUpdate(BaseModel):
    provider: str
    api_key: str | None = None


# --- Integration config ---


@router.get("/integrations")
def list_integrations():
    return get_all_integration_configs()


@router.get("/integrations/{provider}")
def get_integration(provider: str):
    config = get_integration_config(provider)
    if not config:
        raise HTTPException(status_code=404, detail=f"Integration '{provider}' not found")
    return config


@router.put("/integrations/{provider}")
def update_integration(provider: str, body: IntegrationConfigUpdate):
    return upsert_integration_config(
        provider, enabled=body.enabled, config=body.config_json
    )


@router.delete("/integrations/{provider}", status_code=204)
def remove_integration(provider: str):
    delete_integration_config(provider)


# --- Notification preferences ---


@router.get("/notifications")
def get_notifications():
    return get_notification_preferences()


@router.put("/notifications")
def update_notifications(body: NotificationPrefsUpdate):
    current = get_notification_preferences()
    if body.email_enabled is not None:
        current["email_enabled"] = body.email_enabled
    if body.telegram_enabled is not None:
        current["telegram_enabled"] = body.telegram_enabled
    if body.frequency is not None:
        current["frequency"] = body.frequency
    if body.events is not None:
        current["events"] = body.events
    return update_notification_preferences(current)


# --- AI provider ---


@router.get("/ai")
def get_ai():
    return get_ai_settings()


@router.put("/ai")
def update_ai(body: AISettingsUpdate):
    return update_ai_settings(body.provider, body.api_key)


@router.post("/ai/test")
def test_ai(body: AISettingsUpdate | None = None):
    provider = body.provider if body else None
    return test_ai_connection(provider)
