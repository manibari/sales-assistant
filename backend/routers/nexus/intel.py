"""Nexus intel router."""

import json
import logging

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from services.ai_provider import check_ai_available
from services.nexus.ai.intel_ai import parse_raw_intel, summarize_intel_records, chat_intel
from services.nexus.intel import (
    create_intel,
    get_intel,
    get_intel_by_ids,
    get_all_intel,
    confirm_intel,
    update_intel,
    delete_intel,
    get_intel_entities,
    get_entity_intel,
)
from services.nexus.clients import find_client_by_name
from services.nexus.contacts import get_contacts_by_org
from services.nexus.deals import get_deals_by_client
from services.nexus.documents import get_files_by_intel
from services.nexus.intel import get_intel_linked_deals, get_intel_linked_meetings, link_intel_entity
from services.nexus.materialize import materialize_intel, _normalize_company_name
from services.nexus.partners import find_partner_by_name
from services.nexus.prompts import FOLLOWUP_PROMPT

logger = logging.getLogger(__name__)
router = APIRouter()


class IntelCreate(BaseModel):
    title: str | None = None
    raw_input: str
    input_type: str = "text"
    parsed_json: str | None = None
    source_contact_id: int | None = None


class IntelUpdate(BaseModel):
    title: str | None = None
    raw_input: str | None = None
    parsed_json: str | None = None
    status: str | None = None
    source_contact_id: int | None = None


class IntelConfirm(BaseModel):
    parsed_json: str | None = None


class ChatMessage(BaseModel):
    message: str
    current_parsed: dict | None = None


class IntelSummarize(BaseModel):
    intel_ids: list[int]


def _enrich_from_db(parsed: dict) -> tuple[dict, str]:
    """Look up company_name/partner_name in DB, enrich parsed fields, return context string for AI."""
    context_lines: list[str] = []
    enriched = {**parsed}

    # Client lookup
    company = parsed.get("company_name")
    if company:
        normalized = _normalize_company_name(company)
        clients = find_client_by_name(normalized)
        if clients:
            c = clients[0]
            enriched.setdefault("company_name", c["name"])
            if c.get("industry") and not enriched.get("industry"):
                enriched["industry"] = c["industry"]
            context_lines.append(f"[系統] 已匹配客戶「{c['name']}」(#{c['id']})")
            # Fetch contacts
            contacts = get_contacts_by_org("client", c["id"])
            if contacts:
                names = [
                    f"{ct['name']}（{ct.get('title') or '無職稱'}）"
                    for ct in contacts[:5]
                ]
                context_lines.append(f"[系統] 該客戶已有聯絡人：{'、'.join(names)}")
                # Auto-fill first contact if not set
                if not enriched.get("contact_name") and contacts:
                    enriched["contact_name"] = contacts[0]["name"]
                    if contacts[0].get("title"):
                        enriched.setdefault("contact_title", contacts[0]["title"])
                    if contacts[0].get("email"):
                        enriched.setdefault("contact_email", contacts[0]["email"])
                    if contacts[0].get("phone"):
                        enriched.setdefault("contact_phone", contacts[0]["phone"])
            # Fetch deals
            deals = get_deals_by_client(c["id"])
            if deals:
                deal_names = [f"「{d['name']}」({d['stage']})" for d in deals[:3]]
                context_lines.append(f"[系統] 該客戶已有商機：{'、'.join(deal_names)}")

    # Partner lookup
    partner = parsed.get("partner_name")
    if partner:
        normalized = _normalize_company_name(partner)
        partners = find_partner_by_name(normalized)
        if partners:
            p = partners[0]
            enriched.setdefault("partner_name", p["name"])
            context_lines.append(f"[系統] 已匹配夥伴「{p['name']}」(#{p['id']})")
            contacts = get_contacts_by_org("partner", p["id"])
            if contacts:
                names = [
                    f"{ct['name']}（{ct.get('title') or '無職稱'}）"
                    for ct in contacts[:5]
                ]
                context_lines.append(f"[系統] 該夥伴已有聯絡人：{'、'.join(names)}")

    return enriched, "\n".join(context_lines)


@router.get("/")
def list_intel(status: str | None = None, limit: int = 50):
    return get_all_intel(status, limit)


@router.get("/by-entity/{entity_type}/{entity_id}")
def intel_by_entity(entity_type: str, entity_id: int):
    """Get all intel linked to a specific entity (client, partner, contact, deal)."""
    return get_entity_intel(entity_type, entity_id)


@router.post("/summarize")
def summarize_intel(body: IntelSummarize):
    """AI-generated summary from multiple intel records."""
    if not body.intel_ids:
        raise HTTPException(422, "No intel IDs provided")

    if not check_ai_available():
        raise HTTPException(503, "AI service not available")

    intels = get_intel_by_ids(body.intel_ids)
    if not intels:
        raise HTTPException(404, "No intel found for given IDs")

    # Compose user prompt from all intel
    sections = []
    for i, intel in enumerate(intels, 1):
        section = f"--- 情報 #{intel['id']} ({intel.get('created_at', '')}) ---\n{intel['raw_input']}"
        if intel.get("parsed_json"):
            try:
                parsed = (
                    json.loads(intel["parsed_json"])
                    if isinstance(intel["parsed_json"], str)
                    else intel["parsed_json"]
                )
                section += f"\n[已解析欄位] {json.dumps(parsed, ensure_ascii=False)}"
            except (json.JSONDecodeError, TypeError):
                pass
        sections.append(section)

    user_prompt = "\n\n".join(sections)
    # Truncate to avoid token limits
    if len(user_prompt) > 8000:
        user_prompt = user_prompt[:8000] + "\n\n（內容已截斷）"

    summary = summarize_intel_records(user_prompt)

    return {
        "summary": summary.strip(),
        "intel_count": len(intels),
        "intel_ids": [i["id"] for i in intels],
    }


@router.get("/{intel_id}")
def read_intel(intel_id: int):
    intel = get_intel(intel_id)
    if not intel:
        raise HTTPException(404, "Intel not found")
    intel["files"] = get_files_by_intel(intel_id)
    intel["linked_deals"] = get_intel_linked_deals(intel_id)
    intel["linked_meetings"] = get_intel_linked_meetings(intel_id)
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


class LinkMeetingBody(BaseModel):
    meeting_id: int


@router.post("/{intel_id}/meetings")
def link_meeting(intel_id: int, body: LinkMeetingBody):
    return link_intel_entity(intel_id, "meeting", body.meeting_id, "linked")


@router.delete("/{intel_id}/meetings/{meeting_id}", status_code=204)
def unlink_meeting(intel_id: int, meeting_id: int):
    from services.nexus.intel import get_connection
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """DELETE FROM nx_intel_entity
                   WHERE intel_id = %s AND entity_type = 'meeting' AND entity_id = %s""",
                (intel_id, meeting_id),
            )
    return Response(status_code=204)


@router.post("/{intel_id}/parse")
def initial_parse(intel_id: int):
    """Run AI initial parse on raw_input, return parsed JSON + AI greeting."""
    intel = get_intel(intel_id)
    if not intel:
        raise HTTPException(404, "Intel not found")

    if not check_ai_available():
        raise HTTPException(503, "AI service not available")

    raw = intel["raw_input"]
    parsed = parse_raw_intel(raw)

    # Enrich from DB
    parsed, db_context = _enrich_from_db(parsed)

    # Save parsed to intel
    update_intel(intel_id, parsed_json=json.dumps(parsed, ensure_ascii=False))

    # Generate greeting via multi-turn chat
    system = FOLLOWUP_PROMPT
    if db_context:
        system += f"\n\n[SYSTEM NOTE] 以下是系統自動從資料庫補齊的資訊，不需要再問這些：\n{db_context}"

    # Inject current parsed state as context in the first user message
    context_note = f"\n\n[已解析欄位]\n{json.dumps(parsed, ensure_ascii=False, indent=2)}"
    messages = [
        {"role": "user", "content": raw + context_note},
    ]

    greeting_raw = chat_intel(system, messages)

    # Split on --- to get reply part
    ai_reply = (
        greeting_raw.split("---")[0].strip()
        if "---" in greeting_raw
        else greeting_raw.strip()
    )

    # Prepend DB enrichment info to AI reply
    if db_context:
        system_note = db_context.replace("[系統] ", "✅ ")
        ai_reply = f"{system_note}\n\n{ai_reply}"

    # Save chat history
    chat_history = [
        {"role": "user", "text": raw},
        {"role": "assistant", "text": ai_reply},
    ]
    update_intel(intel_id, chat_history=json.dumps(chat_history, ensure_ascii=False))

    return {"parsed": parsed, "ai_reply": ai_reply}


@router.post("/{intel_id}/chat")
def chat_followup(intel_id: int, body: ChatMessage):
    """Conversational followup — multi-turn chat with native messages."""
    intel = get_intel(intel_id)
    if not intel:
        raise HTTPException(404, "Intel not found")

    if not check_ai_available():
        raise HTTPException(503, "AI service not available")

    current = body.current_parsed or {}

    # Enrich current parsed with DB data before sending to AI
    enriched_before, _ = _enrich_from_db(current)

    # Build native multi-turn messages from chat history
    existing_history = []
    if intel.get("chat_history"):
        try:
            existing_history = (
                json.loads(intel["chat_history"])
                if isinstance(intel["chat_history"], str)
                else intel["chat_history"]
            )
        except (json.JSONDecodeError, TypeError):
            pass

    # Convert stored history to API messages format
    # Keep last 10 messages to avoid token bloat
    recent = existing_history[-10:]
    api_messages: list[dict[str, str]] = []
    for msg in recent:
        role = "user" if msg["role"] == "user" else "assistant"
        api_messages.append({"role": role, "content": msg["text"]})

    # Add current user message with parsed state context
    context_note = f"\n\n[目前已知欄位]\n{json.dumps(enriched_before, ensure_ascii=False, indent=2)}"
    api_messages.append({"role": "user", "content": body.message + context_note})

    # Build system prompt
    system = FOLLOWUP_PROMPT

    ai_raw = chat_intel(system, api_messages)

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
            logger.warning(
                "Chat parse failed for intel #%d: %s", intel_id, json_part[:200]
            )

    # Merge new fields into current
    merged = {**enriched_before}
    for k, v in new_fields.items():
        if v is not None:
            merged[k] = v

    # Enrich again after merge (new company_name may have been added)
    _, db_context_before = _enrich_from_db(enriched_before)
    merged, db_context_after = _enrich_from_db(merged)

    # Only show DB enrichment if NEW entities were found
    new_db_lines = set((db_context_after or "").split("\n")) - set(
        (db_context_before or "").split("\n")
    )
    new_db_context = "\n".join(line for line in new_db_lines if line.strip())
    if new_db_context:
        system_note = new_db_context.replace("[系統] ", "✅ ")
        ai_reply = f"{system_note}\n\n{ai_reply}"

    existing_history.append({"role": "user", "text": body.message})
    existing_history.append({"role": "assistant", "text": ai_reply})

    update_intel(
        intel_id,
        parsed_json=json.dumps(merged, ensure_ascii=False),
        chat_history=json.dumps(existing_history, ensure_ascii=False),
    )

    return {"ai_reply": ai_reply, "new_fields": new_fields, "parsed": merged}


class BulkDeleteRequest(BaseModel):
    ids: list[int]


@router.post("/bulk-delete", status_code=204)
def bulk_delete(body: BulkDeleteRequest):
    for intel_id in body.ids:
        delete_intel(intel_id)
    return Response(status_code=204)


@router.delete("/{intel_id}", status_code=204)
def remove_intel(intel_id: int):
    # Treat delete as idempotent so stale UI items do not surface as errors.
    delete_intel(intel_id)
    return Response(status_code=204)
