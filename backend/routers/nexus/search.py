"""Nexus search router — global keyword search."""

from fastapi import APIRouter, HTTPException

from services.nexus.search import global_search, search_intel_by_field

router = APIRouter()


@router.get("/")
def search(q: str, limit: int = 20):
    if not q or len(q.strip()) < 1:
        raise HTTPException(400, "Query parameter 'q' is required")
    return global_search(q.strip(), limit)


@router.get("/intel-fields")
def search_fields(key: str, value: str, limit: int = 50):
    """Search intel by specific parsed field key/value."""
    if not key or not value:
        raise HTTPException(400, "Both 'key' and 'value' parameters are required")
    return search_intel_by_field(key.strip(), value.strip(), limit)
