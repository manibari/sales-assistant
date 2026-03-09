"""Nexus documents router — NDA/MOU tracking + file uploads."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.nexus.documents import (
    get_documents_by_client, update_document, get_expiring_documents,
    create_file, get_files_by_deal, update_file_parse, get_file, delete_file,
)

router = APIRouter()


class DocumentUpdate(BaseModel):
    status: str | None = None
    sign_date: str | None = None
    expiry_date: str | None = None
    file_path: str | None = None
    notes: str | None = None


class FileCreate(BaseModel):
    deal_id: int
    file_type: str
    file_name: str
    file_path: str
    file_size: int | None = None
    source_url: str | None = None


class FileParse(BaseModel):
    parsed_json: str
    parse_status: str = "parsed"


# --- NDA/MOU Documents ---

@router.get("/nda-mou")
def list_documents(client_id: int | None = None):
    if client_id:
        return get_documents_by_client(client_id)
    return []


@router.get("/nda-mou/expiring")
def expiring_documents(within_days: int = 30):
    return get_expiring_documents(within_days)


@router.patch("/nda-mou/{doc_id}")
def patch_document(doc_id: int, body: DocumentUpdate):
    fields = body.model_dump(exclude_none=True)
    result = update_document(doc_id, **fields)
    if not result:
        raise HTTPException(404, "Document not found")
    return result


# --- Files ---

@router.get("/files")
def list_files(deal_id: int):
    return get_files_by_deal(deal_id)


@router.get("/files/{file_id}")
def read_file(file_id: int):
    f = get_file(file_id)
    if not f:
        raise HTTPException(404, "File not found")
    return f


@router.post("/files", status_code=201)
def create_file_endpoint(body: FileCreate):
    return create_file(**body.model_dump())


@router.post("/files/{file_id}/parse")
def parse_file(file_id: int, body: FileParse):
    result = update_file_parse(file_id, body.parsed_json, body.parse_status)
    if not result:
        raise HTTPException(404, "File not found")
    return result


@router.delete("/files/{file_id}", status_code=204)
def remove_file(file_id: int):
    if not delete_file(file_id):
        raise HTTPException(404, "File not found")
