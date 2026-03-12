"""Nexus subsidies router — government grants / subsidy tracking."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.nexus.subsidies import (
    create_subsidy, get_subsidy, get_all_subsidies,
    get_subsidies_by_client, update_subsidy, advance_stage,
    close_subsidy, link_deal, unlink_deal, get_subsidy_deals,
    get_subsidies_expiring_soon,
    add_deadline, get_deadlines, update_deadline, delete_deadline,
)
from services.nexus.intel import get_entity_intel

router = APIRouter()


class SubsidyCreate(BaseModel):
    name: str
    program_type: str = "other"
    source: str | None = None
    agency: str | None = None
    deadline: str | None = None
    funding_amount: str | None = None
    eligibility: str | None = None
    scope: str | None = None
    required_docs: str | None = None
    reference_url: str | None = None
    client_id: int | None = None
    partner_id: int | None = None
    notes: str | None = None


class SubsidyUpdate(BaseModel):
    name: str | None = None
    source: str | None = None
    agency: str | None = None
    program_type: str | None = None
    eligibility: str | None = None
    funding_amount: str | None = None
    scope: str | None = None
    required_docs: str | None = None
    deadline: str | None = None
    reference_url: str | None = None
    stage: str | None = None
    client_id: int | None = None
    partner_id: int | None = None
    notes: str | None = None


class SubsidyClose(BaseModel):
    notes: str | None = None


class DeadlineCreate(BaseModel):
    label: str
    deadline_date: str
    notes: str | None = None
    status: str = "open"


class DeadlineUpdate(BaseModel):
    label: str | None = None
    deadline_date: str | None = None
    notes: str | None = None
    status: str | None = None


class SubsidyDealLink(BaseModel):
    deal_id: int


@router.get("/")
def list_subsidies(
    status: str = "active",
    view: str = "stage",
    client_id: int | None = None,
):
    if client_id:
        return get_subsidies_by_client(client_id)
    return get_all_subsidies(status, view)


@router.get("/expiring")
def expiring(within_days: int = 30):
    return get_subsidies_expiring_soon(within_days)


@router.get("/{subsidy_id}")
def read_subsidy(subsidy_id: int):
    sub = get_subsidy(subsidy_id)
    if not sub:
        raise HTTPException(404, "Subsidy not found")
    sub["deals"] = get_subsidy_deals(subsidy_id)
    sub["intel"] = get_entity_intel("subsidy", subsidy_id)
    sub["deadlines"] = get_deadlines(subsidy_id)
    return sub


@router.post("/", status_code=201)
def create(body: SubsidyCreate):
    return create_subsidy(**body.model_dump())


@router.patch("/{subsidy_id}")
def patch_subsidy(subsidy_id: int, body: SubsidyUpdate):
    fields = body.model_dump(exclude_none=True)
    result = update_subsidy(subsidy_id, **fields)
    if not result:
        raise HTTPException(404, "Subsidy not found")
    return result


@router.post("/{subsidy_id}/advance")
def advance(subsidy_id: int, stage: str):
    try:
        result = advance_stage(subsidy_id, stage)
    except ValueError as e:
        raise HTTPException(400, str(e))
    if not result:
        raise HTTPException(404, "Subsidy not found")
    return result


@router.post("/{subsidy_id}/close")
def close(subsidy_id: int, body: SubsidyClose):
    result = close_subsidy(subsidy_id, body.notes)
    if not result:
        raise HTTPException(404, "Subsidy not found")
    return result


@router.post("/{subsidy_id}/deals", status_code=201)
def link_deal_to_subsidy(subsidy_id: int, body: SubsidyDealLink):
    return link_deal(subsidy_id, body.deal_id)


@router.delete("/{subsidy_id}/deals/{deal_id}", status_code=204)
def unlink_deal_from_subsidy(subsidy_id: int, deal_id: int):
    if not unlink_deal(subsidy_id, deal_id):
        raise HTTPException(404, "Deal not linked to this subsidy")


# --- Deadline endpoints ---

@router.get("/{subsidy_id}/deadlines")
def list_deadlines(subsidy_id: int):
    return get_deadlines(subsidy_id)


@router.post("/{subsidy_id}/deadlines", status_code=201)
def create_deadline(subsidy_id: int, body: DeadlineCreate):
    return add_deadline(subsidy_id, body.label, body.deadline_date, body.notes, body.status)


@router.patch("/{subsidy_id}/deadlines/{deadline_id}")
def patch_deadline(subsidy_id: int, deadline_id: int, body: DeadlineUpdate):
    fields = body.model_dump(exclude_none=True)
    result = update_deadline(deadline_id, **fields)
    if not result:
        raise HTTPException(404, "Deadline not found")
    return result


@router.delete("/{subsidy_id}/deadlines/{deadline_id}", status_code=204)
def remove_deadline(subsidy_id: int, deadline_id: int):
    if not delete_deadline(deadline_id):
        raise HTTPException(404, "Deadline not found")
