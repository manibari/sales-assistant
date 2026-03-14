"""Nexus deals router — the core entity."""

import json
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.ai_provider import check_ai_available, generate_ai_response
from services.nexus.deals import (
    create_deal, get_deal, get_all_deals, get_deals_by_urgency,
    get_deals_needing_push, get_deals_by_client, get_deals_by_partner,
    update_deal, advance_stage, close_deal,
    get_meddic_progress, add_partner_to_deal, get_deal_partners,
    remove_partner_from_deal, link_intel_to_deal, get_deal_intel,
    unlink_intel_from_deal, MEDDIC_KEYS,
)
from services.nexus.tbd import get_open_tbds
from services.nexus.documents import get_files_by_deal
from services.nexus.tags import get_entity_tags

logger = logging.getLogger(__name__)

router = APIRouter()


class DealCreate(BaseModel):
    name: str
    client_id: int
    budget_range: str | None = None
    timeline: str | None = None
    budget_amount: float | None = None
    budget_year: int | None = None


class DealUpdate(BaseModel):
    name: str | None = None
    budget_range: str | None = None
    timeline: str | None = None
    meddic_json: str | None = None
    budget_amount: float | None = None
    budget_year: int | None = None
    created_at: str | None = None


class DealClose(BaseModel):
    reason: str
    notes: str | None = None


class DealPartnerAdd(BaseModel):
    partner_id: int
    role: str | None = None


class DealIntelLink(BaseModel):
    intel_id: int


@router.get("/")
def list_deals(
    status: str = "active",
    view: str = "urgency",
    client_id: int | None = None,
    partner_id: int | None = None,
):
    if client_id:
        return get_deals_by_client(client_id)
    if partner_id:
        return get_deals_by_partner(partner_id)
    if view == "urgency":
        return get_deals_by_urgency()
    return get_all_deals(status)


@router.get("/needs-push")
def needs_push(threshold_days: int = 14):
    return get_deals_needing_push(threshold_days)


@router.get("/{deal_id}")
def read_deal(deal_id: int):
    deal = get_deal(deal_id)
    if not deal:
        raise HTTPException(404, "Deal not found")
    deal["partners"] = get_deal_partners(deal_id)
    deal["intel"] = get_deal_intel(deal_id)
    deal["tbds"] = get_open_tbds("deal", deal_id)
    deal["files"] = get_files_by_deal(deal_id)
    deal["tags"] = get_entity_tags("deal", deal_id)
    deal["meddic_progress"] = get_meddic_progress(deal_id)
    return deal


@router.post("/", status_code=201)
def create(body: DealCreate):
    return create_deal(**body.model_dump())


@router.patch("/{deal_id}")
def patch_deal(deal_id: int, body: DealUpdate):
    fields = body.model_dump(exclude_none=True)
    result = update_deal(deal_id, **fields)
    if not result:
        raise HTTPException(404, "Deal not found")
    return result


@router.post("/{deal_id}/advance")
def advance(deal_id: int, stage: str):
    try:
        result = advance_stage(deal_id, stage)
    except ValueError as e:
        raise HTTPException(400, str(e))
    if not result:
        raise HTTPException(404, "Deal not found")
    return result


@router.post("/{deal_id}/close")
def close(deal_id: int, body: DealClose):
    result = close_deal(deal_id, body.reason, body.notes)
    if not result:
        raise HTTPException(404, "Deal not found")
    return result


@router.get("/{deal_id}/meddic")
def meddic(deal_id: int):
    return get_meddic_progress(deal_id)


# --- Deal-Partner M2M ---

@router.get("/{deal_id}/partners")
def list_deal_partners(deal_id: int):
    return get_deal_partners(deal_id)


@router.post("/{deal_id}/partners", status_code=201)
def add_partner(deal_id: int, body: DealPartnerAdd):
    return add_partner_to_deal(deal_id, body.partner_id, body.role)


@router.delete("/{deal_id}/partners/{partner_id}", status_code=204)
def remove_partner(deal_id: int, partner_id: int):
    if not remove_partner_from_deal(deal_id, partner_id):
        raise HTTPException(404, "Partner not linked to this deal")


# --- Deal-Intel M2M ---

@router.get("/{deal_id}/intel")
def list_deal_intel(deal_id: int):
    return get_deal_intel(deal_id)


@router.post("/{deal_id}/intel", status_code=201)
def link_intel(deal_id: int, body: DealIntelLink):
    return link_intel_to_deal(deal_id, body.intel_id)


@router.delete("/{deal_id}/intel/{intel_id}", status_code=204)
def unlink_intel(deal_id: int, intel_id: int):
    if not unlink_intel_from_deal(deal_id, intel_id):
        raise HTTPException(404, "Intel not linked to this deal")


MEDDIC_AI_PROMPT = """你是 B2B 銷售方法論 MEDDIC 專家。根據以下情報內容，分析並填寫 MEDDIC 六個維度。

MEDDIC 維度：
- metrics: 量化指標 — 客戶期望的具體效益指標（例如：降低30%成本、提升20%良率）
- economic_buyer: 經濟決策者 — 誰有最終預算決定權
- decision_criteria: 決策標準 — 客戶用什麼標準評估方案（技術規格、價格、服務）
- decision_process: 決策流程 — 評估和採購的步驟和時程
- identify_pain: 痛點辨識 — 客戶面臨的核心問題
- champion: 內部擁護者 — 內部支持我方方案的關鍵人物

回覆格式：只輸出 JSON，key 為上述六個維度，value 為繁體中文描述。
如果某維度在情報中找不到線索，該 key 的 value 設為 null。
不要輸出任何 JSON 以外的內容。"""


@router.post("/{deal_id}/meddic/ai-fill")
def ai_fill_meddic(deal_id: int):
    """Use AI to analyze linked intel and fill MEDDIC gaps."""
    deal = get_deal(deal_id)
    if not deal:
        raise HTTPException(404, "Deal not found")

    if not check_ai_available():
        raise HTTPException(503, "AI service not available")

    # Gather all linked intel
    intels = get_deal_intel(deal_id)
    if not intels:
        raise HTTPException(422, "No intel linked to this deal")

    # Compose context from all intel
    sections = []
    for i in intels:
        section = f"[情報 #{i.get('intel_id', i['id'])}] {i['raw_input']}"
        if i.get("parsed_json"):
            try:
                parsed = json.loads(i["parsed_json"]) if isinstance(i["parsed_json"], str) else i["parsed_json"]
                section += f"\n解析欄位: {json.dumps(parsed, ensure_ascii=False)}"
            except (json.JSONDecodeError, TypeError):
                pass
        sections.append(section)

    user_prompt = f"商機名稱：{deal['name']}\n\n" + "\n\n".join(sections)
    if len(user_prompt) > 6000:
        user_prompt = user_prompt[:6000] + "\n（已截斷）"

    ai_raw = generate_ai_response(MEDDIC_AI_PROMPT, user_prompt)

    # Parse AI response
    ai_fields = {}
    try:
        cleaned = ai_raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
        ai_fields = json.loads(cleaned)
    except (json.JSONDecodeError, IndexError):
        logger.warning("MEDDIC AI parse failed: %s", ai_raw[:200])
        raise HTTPException(500, "AI response parse failed")

    # Merge with existing MEDDIC (only fill gaps)
    meddic_raw = deal.get("meddic_json")
    try:
        meddic = json.loads(meddic_raw) if meddic_raw else {}
    except (json.JSONDecodeError, TypeError):
        meddic = {}

    filled = []
    for k in MEDDIC_KEYS:
        if not meddic.get(k) and ai_fields.get(k):
            meddic[k] = ai_fields[k]
            filled.append(k)

    if filled:
        update_deal(deal_id, meddic_json=json.dumps(meddic, ensure_ascii=False))

    return {"meddic": meddic, "ai_filled": filled, "unchanged": [k for k in MEDDIC_KEYS if k not in filled]}
