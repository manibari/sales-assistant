"""Nexus intel router."""

import json
import logging

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from services.ai_provider import check_ai_available, generate_ai_response
from services.nexus.intel import (
    create_intel, get_intel, get_all_intel, confirm_intel, update_intel, delete_intel,
    get_intel_entities, get_entity_intel,
)
from services.nexus.documents import get_files_by_intel
from services.nexus.intel import get_intel_linked_deals
from services.nexus.materialize import materialize_intel

logger = logging.getLogger(__name__)
router = APIRouter()

# Reuse prompts from telegram module
from backend.routers.nexus.telegram import INTEL_PARSE_PROMPT, FOLLOWUP_PROMPT


class IntelCreate(BaseModel):
    raw_input: str
    input_type: str = "text"
    parsed_json: str | None = None
    source_contact_id: int | None = None


class IntelUpdate(BaseModel):
    raw_input: str | None = None
    parsed_json: str | None = None
    status: str | None = None
    source_contact_id: int | None = None


class IntelConfirm(BaseModel):
    parsed_json: str | None = None


class ChatMessage(BaseModel):
    message: str
    current_parsed: dict | None = None


@router.get("/")
def list_intel(status: str | None = None, limit: int = 50):
    return get_all_intel(status, limit)


@router.get("/by-entity/{entity_type}/{entity_id}")
def intel_by_entity(entity_type: str, entity_id: int):
    """Get all intel linked to a specific entity (client, partner, contact, deal)."""
    return get_entity_intel(entity_type, entity_id)


@router.get("/{intel_id}")
def read_intel(intel_id: int):
    intel = get_intel(intel_id)
    if not intel:
        raise HTTPException(404, "Intel not found")
    intel["files"] = get_files_by_intel(intel_id)
    intel["linked_deals"] = get_intel_linked_deals(intel_id)
    return intel


@router.post("/", status_code=201)
def create(body: IntelCreate):
    return create_intel(**body.model_dump())


@router.post("/{intel_id}/confirm")
def confirm(intel_id: int, body: IntelConfirm):
    result = confirm_intel(intel_id, body.parsed_json)
    if not result:
        raise HTTPException(404, "Intel not found")
    return result


@router.patch("/{intel_id}")
def patch_intel(intel_id: int, body: IntelUpdate):
    fields = body.model_dump(exclude_none=True)
    result = update_intel(intel_id, **fields)
    if not result:
        raise HTTPException(404, "Intel not found")
    return result


@router.post("/{intel_id}/materialize")
def materialize(intel_id: int):
    """Manually trigger materialization (useful for re-processing old intel)."""
    intel = get_intel(intel_id)
    if not intel:
        raise HTTPException(404, "Intel not found")
    return materialize_intel(intel_id)


@router.get("/{intel_id}/entities")
def entities(intel_id: int):
    """Get all entities linked to this intel."""
    intel = get_intel(intel_id)
    if not intel:
        raise HTTPException(404, "Intel not found")
    return get_intel_entities(intel_id)


@router.post("/{intel_id}/parse")
def initial_parse(intel_id: int):
    """Run AI initial parse on raw_input, return parsed JSON + AI greeting."""
    intel = get_intel(intel_id)
    if not intel:
        raise HTTPException(404, "Intel not found")

    if not check_ai_available():
        raise HTTPException(503, "AI service not available")

    raw = intel["raw_input"]
    ai_raw = generate_ai_response(INTEL_PARSE_PROMPT, raw)

    parsed = {}
    try:
        cleaned = ai_raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
        parsed = json.loads(cleaned)
    except (json.JSONDecodeError, IndexError):
        logger.warning("Initial parse failed for intel #%d: %s", intel_id, ai_raw[:200])

    # Save parsed to intel
    update_intel(intel_id, parsed_json=json.dumps(parsed, ensure_ascii=False))

    # Generate greeting via followup prompt
    greeting_prompt = FOLLOWUP_PROMPT.format(
        current_json=json.dumps(parsed, ensure_ascii=False, indent=2),
        user_msg="（使用者剛輸入了情報原文，請根據已解析的內容做簡短摘要，並問第一個追問）",
    )
    greeting_raw = generate_ai_response(
        "You are a B2B sales assistant chatbot. Reply in Traditional Chinese.",
        greeting_prompt,
    )
    # Split on --- to get reply part
    ai_reply = greeting_raw.split("---")[0].strip() if "---" in greeting_raw else greeting_raw.strip()

    return {"parsed": parsed, "ai_reply": ai_reply}


@router.post("/{intel_id}/chat")
def chat_followup(intel_id: int, body: ChatMessage):
    """Conversational followup — AI asks questions, user replies, returns updated fields."""
    intel = get_intel(intel_id)
    if not intel:
        raise HTTPException(404, "Intel not found")

    if not check_ai_available():
        raise HTTPException(503, "AI service not available")

    current = body.current_parsed or {}
    prompt = FOLLOWUP_PROMPT.format(
        current_json=json.dumps(current, ensure_ascii=False, indent=2),
        user_msg=body.message,
    )
    ai_raw = generate_ai_response(
        "You are a B2B sales assistant chatbot. Reply in Traditional Chinese.",
        prompt,
    )

    ai_reply = ai_raw.strip()
    new_fields = {}

    if "---" in ai_raw:
        parts = ai_raw.split("---", 1)
        ai_reply = parts[0].strip()
        json_part = parts[1].strip()
        try:
            if json_part.startswith("```"):
                json_part = json_part.split("\n", 1)[1].rsplit("```", 1)[0]
            new_fields = json.loads(json_part)
        except (json.JSONDecodeError, IndexError):
            logger.warning("Chat parse failed for intel #%d: %s", intel_id, json_part[:200])

    # Merge new fields into current
    merged = {**current}
    for k, v in new_fields.items():
        if v is not None:
            merged[k] = v

    # Save to intel
    update_intel(intel_id, parsed_json=json.dumps(merged, ensure_ascii=False))

    return {"ai_reply": ai_reply, "new_fields": new_fields, "parsed": merged}


@router.delete("/{intel_id}", status_code=204)
def remove_intel(intel_id: int):
    # Treat delete as idempotent so stale UI items do not surface as errors.
    delete_intel(intel_id)
    return Response(status_code=204)
