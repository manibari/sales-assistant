"""Nexus tenders router — API backed by markdown files with enrichment."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.nexus.tenders import (
    get_all_tenders,
    get_tender,
    get_tenders_expiring,
    enrich_tender,
    enrich_all_active,
    import_from_pcc_url,
    update_tracking_status,
    TRACKING_STATUSES,
    TRACKING_STATUS_LABELS,
)

router = APIRouter()


@router.get("/")
def list_tenders(
    status: str = "active",
    category: str | None = None,
    tracking_status: str | None = None,
):
    tenders = get_all_tenders(status, category, tracking_status)
    # Strip body_md from list response (too large)
    return [{k: v for k, v in t.items() if k != "body_md"} for t in tenders]


@router.get("/tracking-statuses")
def list_tracking_statuses():
    """Return available tracking statuses with labels."""
    return [
        {"key": k, "label": v}
        for k, v in TRACKING_STATUS_LABELS.items()
    ]


@router.get("/expiring")
def expiring(within_days: int = 30):
    return get_tenders_expiring(within_days)


class UpdateTrackingStatusRequest(BaseModel):
    tracking_status: str


@router.patch("/{job_number}/tracking-status")
def patch_tracking_status(job_number: str, body: UpdateTrackingStatusRequest):
    """Update a tender's tracking status."""
    try:
        return update_tracking_status(job_number, body.tracking_status)
    except FileNotFoundError:
        raise HTTPException(404, f"Tender {job_number} not found")
    except ValueError as e:
        raise HTTPException(400, str(e))


class ImportPccRequest(BaseModel):
    url: str


@router.post("/import-pcc")
def import_pcc(body: ImportPccRequest):
    """Import a tender directly from a pcc.gov.tw URL."""
    try:
        result = import_from_pcc_url(body.url)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/enrich-all")
def enrich_all():
    """Enrich all active tenders with pcc.gov.tw page content + notice documents."""
    results = enrich_all_active()
    return {"results": results}


@router.post("/{job_number}/enrich")
def enrich(job_number: str):
    """Enrich a single tender with full content from pcc.gov.tw."""
    try:
        return enrich_tender(job_number)
    except FileNotFoundError:
        raise HTTPException(404, f"Tender {job_number} not found")
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/{job_number}")
def read_tender(job_number: str):
    t = get_tender(job_number)
    if not t:
        raise HTTPException(404, "Tender not found")
    return t
