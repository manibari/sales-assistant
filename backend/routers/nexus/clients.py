"""Nexus clients router."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.nexus.clients import (
    create_client, get_client, get_all_clients, update_client, delete_client,
)
from services.nexus.documents import get_documents_by_client
from services.nexus.tags import get_entity_tags

router = APIRouter()


class ClientCreate(BaseModel):
    name: str
    industry: str | None = None
    budget_range: str | None = None
    notes: str | None = None


class ClientUpdate(BaseModel):
    name: str | None = None
    industry: str | None = None
    budget_range: str | None = None
    status: str | None = None
    notes: str | None = None


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


@router.delete("/{client_id}", status_code=204)
def remove_client(client_id: int):
    if not delete_client(client_id):
        raise HTTPException(404, "Client not found")
