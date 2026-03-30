"""Nexus plans router — strategy plans (annual, product, internal, proposal)."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.nexus.plans import (
    create_plan,
    get_plan,
    get_all_plans,
    update_plan,
    archive_plan,
)

router = APIRouter()


class PlanCreate(BaseModel):
    title: str
    plan_type: str = "annual"
    fiscal_year: int | None = None
    body: str | None = None
    deal_id: int | None = None
    client_id: int | None = None
    notes: str | None = None


class PlanUpdate(BaseModel):
    title: str | None = None
    plan_type: str | None = None
    fiscal_year: int | None = None
    body: str | None = None
    deal_id: int | None = None
    client_id: int | None = None
    notes: str | None = None
    status: str | None = None


@router.get("/")
def list_plans(plan_type: str | None = None, status: str | None = None):
    return get_all_plans(plan_type=plan_type, status=status)


@router.get("/{plan_id}")
def read_plan(plan_id: int):
    plan = get_plan(plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")
    return plan


@router.post("/", status_code=201)
def create(body: PlanCreate):
    return create_plan(**body.model_dump())


@router.patch("/{plan_id}")
def patch_plan(plan_id: int, body: PlanUpdate):
    fields = body.model_dump(exclude_none=True)
    result = update_plan(plan_id, **fields)
    if not result:
        raise HTTPException(404, "Plan not found")
    return result


@router.post("/{plan_id}/archive")
def do_archive(plan_id: int):
    result = archive_plan(plan_id)
    if not result:
        raise HTTPException(404, "Plan not found")
    return result
