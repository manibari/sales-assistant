"""Nexus partners router."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.nexus.partners import (
    create_partner, get_partner, get_all_partners, update_partner,
    update_trust_level, delete_partner,
)
from services.nexus.tags import get_entity_tags

router = APIRouter()


class PartnerCreate(BaseModel):
    name: str
    trust_level: str = "unverified"
    team_size: str | None = None
    notes: str | None = None


class PartnerUpdate(BaseModel):
    name: str | None = None
    trust_level: str | None = None
    team_size: str | None = None
    notes: str | None = None


@router.get("/")
def list_partners(trust_level: str | None = None):
    return get_all_partners(trust_level)


@router.get("/{partner_id}")
def read_partner(partner_id: int):
    partner = get_partner(partner_id)
    if not partner:
        raise HTTPException(404, "Partner not found")
    partner["tags"] = get_entity_tags("partner", partner_id)
    return partner


@router.post("/", status_code=201)
def create(body: PartnerCreate):
    return create_partner(**body.model_dump())


@router.patch("/{partner_id}")
def patch_partner(partner_id: int, body: PartnerUpdate):
    fields = body.model_dump(exclude_none=True)
    result = update_partner(partner_id, **fields)
    if not result:
        raise HTTPException(404, "Partner not found")
    return result


@router.patch("/{partner_id}/trust")
def change_trust(partner_id: int, level: str):
    try:
        result = update_trust_level(partner_id, level)
    except ValueError as e:
        raise HTTPException(400, str(e))
    if not result:
        raise HTTPException(404, "Partner not found")
    return result


@router.delete("/{partner_id}", status_code=204)
def remove_partner(partner_id: int):
    if not delete_partner(partner_id):
        raise HTTPException(404, "Partner not found")
