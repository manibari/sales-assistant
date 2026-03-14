"""Nexus intel router."""

import json
import logging

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from services.ai_provider import check_ai_available, generate_ai_response
from services.nexus.intel import (
    create_intel, get_intel, get_intel_by_ids, get_all_intel, confirm_intel, update_intel, delete_intel,
    get_intel_entities, get_entity_intel,
)
from services.nexus.clients import find_client_by_name
from services.nexus.contacts import get_contacts_by_org
from services.nexus.deals import get_deals_by_client
from services.nexus.documents import get_files_by_intel
from services.nexus.intel import get_intel_linked_deals
from services.nexus.materialize import materialize_intel, _normalize_company_name
from services.nexus.partners import find_partner_by_name

logger = logging.getLogger(__name__)
router = APIRouter()

# Reuse prompts from telegram module
from backend.routers.nexus.telegram import INTEL_PARSE_PROMPT, FOLLOWUP_PROMPT


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
                names = [f"{ct['name']}（{ct.get('title') or '無職稱'}）" for ct in contacts[:5]]
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
                names = [f"{ct['name']}（{ct.get('title') or '無職稱'}）" for ct in contacts[:5]]
                context_lines.append(f"[系統] 該夥伴已有聯絡人：{'、'.join(names)}")

    return enriched, "\n".join(context_lines)


@router.get("/")
def list_intel(status: str | None = None, limit: int = 50):
    return get_all_intel(status, limit)


@router.get("/by-entity/{entity_type}/{entity_id}")
def intel_by_entity(entity_type: str, entity_id: int):
    """Get all intel linked to a specific entity (client, partner, contact, deal)."""
    return get_entity_intel(entity_type, entity_id)


INTEL_SUMMARIZE_PROMPT = """你是 B2B 業務情報分析師。根據以下多筆情報原文，產生一份結構化摘要。

格式要求（繁體中文）：
## 關鍵實體
列出所有提到的公司、人物、組織

## 痛點與需求
客戶面臨的問題和需求

## 時程與預算
任何提到的時間線、預算範圍、年度

## 關鍵聯絡人
提到的決策者、聯絡窗口及其角色

## 商機潛力評估
綜合判斷這些情報反映的商機成熟度和下一步建議

如果某個區段沒有相關資訊，請標註「未提及」而非省略。"""


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
                parsed = json.loads(intel["parsed_json"]) if isinstance(intel["parsed_json"], str) else intel["parsed_json"]
                section += f"\n[已解析欄位] {json.dumps(parsed, ensure_ascii=False)}"
            except (json.JSONDecodeError, TypeError):
                pass
        sections.append(section)

    user_prompt = "\n\n".join(sections)
    # Truncate to avoid token limits
    if len(user_prompt) > 8000:
        user_prompt = user_prompt[:8000] + "\n\n（內容已截斷）"

    summary = generate_ai_response(INTEL_SUMMARIZE_PROMPT, user_prompt)

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

    # Enrich from DB
    parsed, db_context = _enrich_from_db(parsed)

    # Save parsed to intel
    update_intel(intel_id, parsed_json=json.dumps(parsed, ensure_ascii=False))

    # Generate greeting via followup prompt, include DB context
    extra_context = ""
    if db_context:
        extra_context = f"\n\n以下是系統自動從資料庫補齊的資訊，不需要再問這些：\n{db_context}"
    greeting_prompt = FOLLOWUP_PROMPT.format(
        current_json=json.dumps(parsed, ensure_ascii=False, indent=2),
        user_msg=f"（使用者剛輸入了情報原文，請根據已解析的內容做簡短摘要，並問第一個追問）{extra_context}",
    )
    greeting_raw = generate_ai_response(
        "You are a B2B sales assistant chatbot. Reply in Traditional Chinese.",
        greeting_prompt,
    )
    # Split on --- to get reply part
    ai_reply = greeting_raw.split("---")[0].strip() if "---" in greeting_raw else greeting_raw.strip()

    # Prepend DB enrichment info to AI reply
    if db_context:
        system_note = db_context.replace("[系統] ", "✅ ")
        ai_reply = f"{system_note}\n\n{ai_reply}"

    # Save chat history
    chat_history = [
        {"role": "user", "text": raw},
        {"role": "ai", "text": ai_reply},
    ]
    update_intel(intel_id, chat_history=json.dumps(chat_history, ensure_ascii=False))

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

    # Enrich current parsed with DB data before sending to AI
    enriched_before, _ = _enrich_from_db(current)

    prompt = FOLLOWUP_PROMPT.format(
        current_json=json.dumps(enriched_before, ensure_ascii=False, indent=2),
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
    merged = {**enriched_before}
    for k, v in new_fields.items():
        if v is not None:
            merged[k] = v

    # Enrich again after merge (new company_name may have been added)
    merged, db_context = _enrich_from_db(merged)

    # Save to intel
    # Append to chat history
    existing_history = []
    if intel.get("chat_history"):
        try:
            existing_history = json.loads(intel["chat_history"]) if isinstance(intel["chat_history"], str) else intel["chat_history"]
        except (json.JSONDecodeError, TypeError):
            pass

    # Prepend DB enrichment info if new entities were found
    if db_context:
        system_note = db_context.replace("[系統] ", "✅ ")
        ai_reply = f"{system_note}\n\n{ai_reply}"

    existing_history.append({"role": "user", "text": body.message})
    existing_history.append({"role": "ai", "text": ai_reply})

    update_intel(
        intel_id,
        parsed_json=json.dumps(merged, ensure_ascii=False),
        chat_history=json.dumps(existing_history, ensure_ascii=False),
    )

    return {"ai_reply": ai_reply, "new_fields": new_fields, "parsed": merged}


@router.delete("/{intel_id}", status_code=204)
def remove_intel(intel_id: int):
    # Treat delete as idempotent so stale UI items do not surface as errors.
    delete_intel(intel_id)
    return Response(status_code=204)
