"""Nexus documents router — NDA/MOU tracking + file uploads."""

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel

from services.nexus.documents import (
    get_all_documents,
    get_documents_by_client,
    update_document,
    get_expiring_documents,
    create_file,
    get_files_by_deal,
    get_files_by_intel,
    update_file,
    update_file_parse,
    get_file,
    delete_file,
)

UPLOADS_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

router = APIRouter()


class DocumentUpdate(BaseModel):
    status: str | None = None
    sign_date: str | None = None
    expiry_date: str | None = None
    file_path: str | None = None
    notes: str | None = None


class FileCreate(BaseModel):
    deal_id: int | None = None
    intel_id: int | None = None
    file_type: str
    file_name: str
    file_path: str
    file_size: int | None = None
    source_url: str | None = None


class FileUpdate(BaseModel):
    file_name: str | None = None
    file_type: str | None = None


class FileParse(BaseModel):
    parsed_json: str
    parse_status: str = "parsed"


# --- NDA/MOU Documents ---


@router.get("/nda-mou")
def list_documents(client_id: int | None = None):
    if client_id:
        return get_documents_by_client(client_id)
    return get_all_documents()


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
def list_files(deal_id: int | None = None, intel_id: int | None = None):
    if intel_id:
        return get_files_by_intel(intel_id)
    if deal_id:
        return get_files_by_deal(deal_id)
    return []


@router.get("/files/{file_id}")
def read_file(file_id: int):
    f = get_file(file_id)
    if not f:
        raise HTTPException(404, "File not found")
    return f


@router.post("/files", status_code=201)
def create_file_endpoint(body: FileCreate):
    return create_file(**body.model_dump())


@router.patch("/files/{file_id}")
def patch_file(file_id: int, body: FileUpdate):
    fields = body.model_dump(exclude_none=True)
    result = update_file(file_id, **fields)
    if not result:
        raise HTTPException(404, "File not found")
    return result


@router.post("/files/{file_id}/parse")
def parse_file(file_id: int, body: FileParse):
    result = update_file_parse(file_id, body.parsed_json, body.parse_status)
    if not result:
        raise HTTPException(404, "File not found")
    return result


@router.get("/files/{file_id}/download")
def download_file(file_id: int):
    f = get_file(file_id)
    if not f:
        raise HTTPException(404, "File not found")
    # External link → redirect
    if f.get("source_url"):
        return RedirectResponse(url=f["source_url"])
    # Local file → serve from uploads/
    file_path = UPLOADS_DIR / os.path.basename(f["file_path"])
    if not file_path.exists():
        raise HTTPException(404, "File not found on disk")
    return FileResponse(
        path=str(file_path),
        filename=f["file_name"],
        media_type="application/octet-stream",
    )


@router.post("/files/upload", status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    deal_id: int | None = Form(None),
    intel_id: int | None = Form(None),
    file_type: str = Form("attachment"),
):
    # Save to uploads/
    safe_name = os.path.basename(file.filename or "upload")
    dest = UPLOADS_DIR / safe_name
    # Avoid overwriting: add suffix if exists
    counter = 1
    while dest.exists():
        stem, ext = os.path.splitext(safe_name)
        dest = UPLOADS_DIR / f"{stem}_{counter}{ext}"
        counter += 1
    contents = await file.read()
    dest.write_bytes(contents)
    # Create DB record
    return create_file(
        deal_id=deal_id,
        intel_id=intel_id,
        file_type=file_type,
        file_name=file.filename or "upload",
        file_path=str(dest.name),
        file_size=len(contents),
    )


@router.delete("/files/{file_id}", status_code=204)
def remove_file(file_id: int):
    if not delete_file(file_id):
        raise HTTPException(404, "File not found")
