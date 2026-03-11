"""Nexus contacts router."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.nexus.contacts import (
    create_contact, get_contact, get_all_contacts, get_contacts_by_org,
    update_contact, delete_contact,
)

router = APIRouter()


class ContactCreate(BaseModel):
    name: str
    org_type: str | None = None
    org_id: int | None = None
    title: str | None = None
    phone: str | None = None
    email: str | None = None
    line_id: str | None = None
    role: str | None = None
    notes: str | None = None


class ContactUpdate(BaseModel):
    name: str | None = None
    title: str | None = None
    phone: str | None = None
    email: str | None = None
    line_id: str | None = None
    org_type: str | None = None
    org_id: int | None = None
    role: str | None = None
    notes: str | None = None


@router.get("/")
def list_contacts(org_type: str | None = None, org_id: int | None = None):
    if org_type and org_id:
        return get_contacts_by_org(org_type, org_id)
    return get_all_contacts()


@router.get("/{contact_id}")
def read_contact(contact_id: int):
    contact = get_contact(contact_id)
    if not contact:
        raise HTTPException(404, "Contact not found")
    return contact


@router.post("/", status_code=201)
def create(body: ContactCreate):
    return create_contact(**body.model_dump())


@router.patch("/{contact_id}")
def patch_contact(contact_id: int, body: ContactUpdate):
    fields = body.model_dump(exclude_none=True)
    result = update_contact(contact_id, **fields)
    if not result:
        raise HTTPException(404, "Contact not found")
    return result


@router.delete("/{contact_id}", status_code=204)
def remove_contact(contact_id: int):
    if not delete_contact(contact_id):
        raise HTTPException(404, "Contact not found")
