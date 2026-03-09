"""Nexus deals router — the core entity."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.nexus.deals import (
    create_deal, get_deal, get_all_deals, get_deals_by_urgency,
    get_deals_needing_push, update_deal, advance_stage, close_deal,
    get_meddic_progress, add_partner_to_deal, get_deal_partners,
    remove_partner_from_deal, link_intel_to_deal, get_deal_intel,
    unlink_intel_from_deal,
)
from services.nexus.tbd import get_open_tbds
from services.nexus.documents import get_files_by_deal
from services.nexus.tags import get_entity_tags

router = APIRouter()


class DealCreate(BaseModel):
    name: str
    client_id: int
    budget_range: str | None = None
    timeline: str | None = None


class DealUpdate(BaseModel):
    name: str | None = None
    budget_range: str | None = None
    timeline: str | None = None
    meddic_json: str | None = None


class DealClose(BaseModel):
    reason: str
    notes: str | None = None


class DealPartnerAdd(BaseModel):
    partner_id: int
    role: str | None = None


class DealIntelLink(BaseModel):
    intel_id: int


@router.get("/")
def list_deals(status: str = "active", view: str = "urgency"):
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
