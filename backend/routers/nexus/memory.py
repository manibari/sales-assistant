"""Nexus memory router — knowledge management API."""

import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from services.nexus.memory import (
    list_memories,
    get_memory,
    create_memory,
    update_memory,
    delete_memory,
    search_memories,
    sync_all,
    promote_memory,
    update_status,
    list_categories,
    list_templates,
    create_from_template,
    migrate_to_inbox,
    _slugify,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class MemoryCreate(BaseModel):
    title: str
    type: str = "manual"
    scope: str = "long-term"
    client: str | None = None
    client_id: int | None = None
    deal_id: int | None = None
    tags: list[str] = []
    body: str = ""
    folder: str | None = None


class MemoryUpdate(BaseModel):
    title: str | None = None
    type: str | None = None
    scope: str | None = None
    client: str | None = None
    client_id: int | None = None
    deal_id: int | None = None
    tags: list[str] | None = None
    body: str | None = None


class PromoteRequest(BaseModel):
    source_path: str
    target_zone: str  # "domain" | "deals"
    category: str
    new_title: str
    new_body: str
    tags: list[str] | None = None


class StatusUpdate(BaseModel):
    path: str
    status: str  # "inbox" | "draft" | "published" | "archived"


class FromTemplateRequest(BaseModel):
    template_name: str
    target_zone: str  # "domain" | "deals"
    category: str
    title: str


@router.get("/")
def list_memories_route(
    scope: str | None = None,
    client_id: int | None = None,
    deal_id: int | None = None,
    type: str | None = Query(None, alias="type"),
    status: str | None = None,
    category: str | None = None,
    zone: str | None = None,
):
    return list_memories(
        scope=scope,
        client_id=client_id,
        deal_id=deal_id,
        type_=type,
        status=status,
        category=category,
        zone=zone,
    )


@router.get("/file")
def get_memory_route(path: str):
    mem = get_memory(path)
    if not mem:
        raise HTTPException(status_code=404, detail="Memory not found")
    return mem


@router.post("/")
def create_memory_route(data: MemoryCreate):
    if data.folder:
        folder = data.folder
    elif data.deal_id:
        folder = f"deals/{_slugify(data.title)}"
    elif data.client:
        folder = f"clients/{_slugify(data.client)}"
    else:
        folder = "general"

    filename = f"{_slugify(data.title)}.md"

    frontmatter = {
        "title": data.title,
        "type": data.type,
        "scope": data.scope,
        "tags": data.tags,
        "source": "manual",
    }
    if data.client:
        frontmatter["client"] = data.client
    if data.client_id is not None:
        frontmatter["client_id"] = data.client_id
    if data.deal_id is not None:
        frontmatter["deal_id"] = data.deal_id

    try:
        return create_memory(folder, filename, frontmatter, data.body)
    except FileExistsError:
        raise HTTPException(status_code=409, detail="Memory already exists")


@router.put("/file")
def update_memory_route(path: str, data: MemoryUpdate):
    existing = get_memory(path)
    if not existing:
        raise HTTPException(status_code=404, detail="Memory not found")

    frontmatter = {k: v for k, v in existing.items() if not k.startswith("_")}
    if data.title is not None:
        frontmatter["title"] = data.title
    if data.type is not None:
        frontmatter["type"] = data.type
    if data.scope is not None:
        frontmatter["scope"] = data.scope
    if data.client is not None:
        frontmatter["client"] = data.client
    if data.client_id is not None:
        frontmatter["client_id"] = data.client_id
    if data.deal_id is not None:
        frontmatter["deal_id"] = data.deal_id
    if data.tags is not None:
        frontmatter["tags"] = data.tags

    body = data.body if data.body is not None else existing.get("_body", "")

    return update_memory(path, frontmatter, body)


@router.delete("/file")
def delete_memory_route(path: str):
    if not delete_memory(path):
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"deleted": path}


@router.get("/search")
def search_memories_route(q: str):
    return search_memories(q)


@router.post("/sync-all")
def sync_all_route():
    stats = sync_all()
    return {"status": "ok", **stats}


# --- New endpoints for knowledge management ---


@router.post("/promote")
def promote_route(data: PromoteRequest):
    try:
        return promote_memory(
            source_path=data.source_path,
            target_zone=data.target_zone,
            category=data.category,
            new_title=data.new_title,
            new_body=data.new_body,
            tags=data.tags,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/status")
def update_status_route(data: StatusUpdate):
    try:
        return update_status(data.path, data.status)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/categories")
def list_categories_route():
    return list_categories()


@router.get("/templates")
def list_templates_route():
    return list_templates()


@router.post("/from-template")
def from_template_route(data: FromTemplateRequest):
    try:
        return create_from_template(
            template_name=data.template_name,
            target_zone=data.target_zone,
            category=data.category,
            title=data.title,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/migrate")
def migrate_route():
    stats = migrate_to_inbox()
    return {"status": "ok", **stats}
