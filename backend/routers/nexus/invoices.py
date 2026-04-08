"""Invoices router — Finance & admin only."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.routers.nexus.auth import get_current_user, require_finance
from services.nexus.invoices import (
    create_invoice,
    get_invoice,
    list_invoices,
    update_invoice,
)

router = APIRouter()


class InvoiceCreate(BaseModel):
    deal_id: int
    client_id: int
    invoice_no: str
    amount: float
    tax_rate: float = 0.05
    currency: str = "TWD"
    issue_date: str | None = None
    due_date: str | None = None
    notes: str | None = None
    project_id: int | None = None
    sow_doc_id: int | None = None
    milestone_index: int | None = None


class InvoiceUpdate(BaseModel):
    status: str | None = None
    paid_date: str | None = None
    issue_date: str | None = None
    due_date: str | None = None
    notes: str | None = None
    amount: float | None = None
    invoice_no: str | None = None
    currency: str | None = None


@router.get("/")
def list_all(
    deal_id: int | None = None,
    client_id: int | None = None,
    project_id: int | None = None,
    status: str | None = None,
    _user: dict = Depends(require_finance),
):
    return list_invoices(deal_id=deal_id, client_id=client_id, project_id=project_id, status=status)


@router.post("/", status_code=201)
def create(body: InvoiceCreate, current_user: dict = Depends(require_finance)):
    try:
        return create_invoice(
            deal_id=body.deal_id,
            client_id=body.client_id,
            invoice_no=body.invoice_no,
            amount=body.amount,
            tax_rate=body.tax_rate,
            issue_date=body.issue_date,
            due_date=body.due_date,
            notes=body.notes,
            created_by=current_user["id"],
            project_id=body.project_id,
            sow_doc_id=body.sow_doc_id,
            milestone_index=body.milestone_index,
        )
    except Exception as e:
        if "unique" in str(e).lower():
            raise HTTPException(409, "Invoice number already exists")
        raise


@router.get("/{invoice_id}")
def read(invoice_id: int, _user: dict = Depends(require_finance)):
    inv = get_invoice(invoice_id)
    if not inv:
        raise HTTPException(404, "Invoice not found")
    return inv


@router.patch("/{invoice_id}")
def update(invoice_id: int, body: InvoiceUpdate, _user: dict = Depends(require_finance)):
    try:
        result = update_invoice(invoice_id, **body.model_dump(exclude_none=True))
    except ValueError as e:
        raise HTTPException(400, str(e))
    if not result:
        raise HTTPException(404, "Invoice not found")
    return result
