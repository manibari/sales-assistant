"""Nexus tags router."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.nexus.tags import (
    create_tag, get_all_tags, tag_entity, untag_entity,
    get_entity_tags, search_by_tag_name,
)

router = APIRouter()


class TagCreate(BaseModel):
    name: str
    category: str


class EntityTag(BaseModel):
    entity_type: str
    entity_id: int
    tag_id: int


@router.get("/")
def list_tags(category: str | None = None):
    return get_all_tags(category)


@router.get("/search")
def search_tags(q: str, category: str | None = None):
    return search_by_tag_name(q, category)


@router.post("/", status_code=201)
def create(body: TagCreate):
    return create_tag(body.name, body.category)


@router.get("/entity/{entity_type}/{entity_id}")
def entity_tags(entity_type: str, entity_id: int):
    return get_entity_tags(entity_type, entity_id)


@router.post("/entity", status_code=201)
def add_tag_to_entity(body: EntityTag):
    return tag_entity(body.entity_type, body.entity_id, body.tag_id)


@router.delete("/entity/{entity_type}/{entity_id}/{tag_id}", status_code=204)
def remove_tag_from_entity(entity_type: str, entity_id: int, tag_id: int):
    if not untag_entity(entity_type, entity_id, tag_id):
        raise HTTPException(404, "Tag not linked to entity")
