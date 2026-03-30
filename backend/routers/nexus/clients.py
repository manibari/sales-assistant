"""Nexus clients router."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.nexus.clients import (
    create_client,
    get_client,
    get_all_clients,
    update_client,
    delete_client,
    merge_clients,
    toggle_pin_client,
)
from services.nexus.documents import get_documents_by_client
from services.nexus.tags import get_entity_tags

router = APIRouter()


class ClientCreate(BaseModel):
    name: str
    industry: str | None = None
    budget_range: str | None = None
    notes: str | None = None
    market: str = "domestic"


class ClientUpdate(BaseModel):
    name: str | None = None
    industry: str | None = None
    budget_range: str | None = None
    status: str | None = None
    notes: str | None = None
    market: str | None = None


@router.get("/")
def list_clients(status: str | None = None):
    return get_all_clients(status)


@router.get("/{client_id}")
def read_client(client_id: int):
    client = get_client(client_id)
    if not client:
        raise HTTPException(404, "Client not found")
    client["documents"] = get_documents_by_client(client_id)
    client["tags"] = get_entity_tags("client", client_id)
    return client


@router.post("/", status_code=201)
def create(body: ClientCreate):
    return create_client(**body.model_dump())


@router.patch("/{client_id}")
def patch_client(client_id: int, body: ClientUpdate):
    fields = body.model_dump(exclude_none=True)
    result = update_client(client_id, **fields)
    if not result:
        raise HTTPException(404, "Client not found")
    return result


@router.post("/{client_id}/pin")
def pin_client(client_id: int):
    result = toggle_pin_client(client_id)
    if not result:
        raise HTTPException(404, "Client not found")
    return result


@router.delete("/{client_id}", status_code=204)
def remove_client(client_id: int):
    result = delete_client(client_id)
    if isinstance(result, str):
        raise HTTPException(409, result)
    if not result:
        raise HTTPException(404, "Client not found")


class MergeRequest(BaseModel):
    target_id: int
    source_ids: list[int]


@router.post("/merge")
def merge(body: MergeRequest):
    """Merge source clients into target. Moves all related data, deletes sources."""
    result = merge_clients(body.target_id, body.source_ids)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result
