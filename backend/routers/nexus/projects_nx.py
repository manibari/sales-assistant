"""Nexus projects router — delivery projects from won deals."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.routers.nexus.auth import get_current_user
from services.nexus.projects_nx import (
    create_project,
    get_project,
    get_project_by_deal,
    list_projects,
    update_project,
)

router = APIRouter()


class ProjectCreate(BaseModel):
    deal_id: int
    client_id: int
    name: str
    postsale_owner: int | None = None
    start_date: str | None = None
    end_date: str | None = None
    notes: str | None = None


class ProjectUpdate(BaseModel):
    status: str | None = None
    postsale_owner: int | None = None
    start_date: str | None = None
    end_date: str | None = None
    notes: str | None = None
    name: str | None = None


@router.get("/")
def list_all(
    status: str | None = None,
    client_id: int | None = None,
    postsale_owner: int | None = None,
    _user: dict = Depends(get_current_user),
):
    return list_projects(status=status, client_id=client_id, postsale_owner=postsale_owner)


@router.post("/", status_code=201)
def create(body: ProjectCreate, _user: dict = Depends(get_current_user)):
    return create_project(**body.model_dump())


@router.get("/by-deal/{deal_id}")
def by_deal(deal_id: int, _user: dict = Depends(get_current_user)):
    proj = get_project_by_deal(deal_id)
    if not proj:
        raise HTTPException(404, "No project found for this deal")
    return proj


@router.get("/{project_id}")
def read(project_id: int, _user: dict = Depends(get_current_user)):
    proj = get_project(project_id)
    if not proj:
        raise HTTPException(404, "Project not found")
    return proj


@router.patch("/{project_id}")
def update(project_id: int, body: ProjectUpdate, _user: dict = Depends(get_current_user)):
    try:
        result = update_project(project_id, **body.model_dump(exclude_none=True))
    except ValueError as e:
        raise HTTPException(400, str(e))
    if not result:
        raise HTTPException(404, "Project not found")
    return result
