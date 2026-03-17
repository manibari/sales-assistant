"""Nexus tenders router — read-only API backed by markdown files."""

from fastapi import APIRouter, HTTPException

from services.nexus.tenders import (
    get_all_tenders,
    get_tender,
    get_tenders_expiring,
)

router = APIRouter()


@router.get("/")
def list_tenders(status: str = "active", category: str | None = None):
    return get_all_tenders(status, category)


@router.get("/expiring")
def expiring(within_days: int = 30):
    return get_tenders_expiring(within_days)


@router.get("/{job_number}")
def read_tender(job_number: str):
    t = get_tender(job_number)
    if not t:
        raise HTTPException(404, "Tender not found")
    return t
