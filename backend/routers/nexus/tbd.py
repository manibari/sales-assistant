"""Nexus TBD router."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.nexus.tbd import (
    create_tbd,
    get_tbd,
    get_open_tbds,
    get_all_tbds,
    resolve_tbd,
    get_stale_tbds,
    delete_tbd,
)

router = APIRouter()


class TbdCreate(BaseModel):
    question: str
    linked_type: str | None = None
    linked_id: int | None = None
    source: str = "skip"
    context: str | None = None


@router.get("/")
def list_tbds(
    linked_type: str | None = None,
    linked_id: int | None = None,
    include_resolved: bool = False,
):
    if linked_type and linked_id:
        return get_open_tbds(linked_type, linked_id)
    return get_all_tbds(include_resolved)


@router.get("/stale")
def stale_tbds(older_than_days: int = 7):
    return get_stale_tbds(older_than_days)


@router.get("/{tbd_id}")
def read_tbd(tbd_id: int):
    tbd = get_tbd(tbd_id)
    if not tbd:
        raise HTTPException(404, "TBD not found")
    return tbd


@router.post("/", status_code=201)
def create(body: TbdCreate):
    return create_tbd(**body.model_dump())


@router.post("/{tbd_id}/resolve")
def resolve(tbd_id: int):
    result = resolve_tbd(tbd_id)
    if not result:
        raise HTTPException(404, "TBD not found")
    return result


@router.delete("/{tbd_id}", status_code=204)
def remove_tbd(tbd_id: int):
    if not delete_tbd(tbd_id):
        raise HTTPException(404, "TBD not found")
