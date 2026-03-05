"""CRM API router — wraps services/crm.py."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services import crm as crm_svc

router = APIRouter()


class ClientCreate(BaseModel):
    client_id: str
    company_name: str
    industry: str | None = None
    department: str | None = None
    email: str | None = None
    notes: str | None = None


@router.get("/")
def list_clients():
    return crm_svc.get_all()


@router.get("/{client_id}")
def get_client(client_id: str):
    result = crm_svc.get_by_id(client_id)
    if not result:
        raise HTTPException(status_code=404, detail="Client not found")
    return result


@router.post("/", status_code=201)
def create_client(body: ClientCreate):
    crm_svc.create(
        client_id=body.client_id,
        company_name=body.company_name,
        industry=body.industry,
        department=body.department,
        email=body.email,
        notes=body.notes,
    )
    return {"client_id": body.client_id}
