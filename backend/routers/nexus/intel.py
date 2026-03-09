"""Nexus intel router."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.nexus.intel import (
    create_intel, get_intel, get_all_intel, confirm_intel, update_intel, delete_intel,
)

router = APIRouter()


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


@router.get("/")
def list_intel(status: str | None = None, limit: int = 50):
    return get_all_intel(status, limit)


@router.get("/{intel_id}")
def read_intel(intel_id: int):
    intel = get_intel(intel_id)
    if not intel:
        raise HTTPException(404, "Intel not found")
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


@router.delete("/{intel_id}", status_code=204)
def remove_intel(intel_id: int):
    if not delete_intel(intel_id):
        raise HTTPException(404, "Intel not found")
