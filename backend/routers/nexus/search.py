"""Nexus search router — global keyword search."""

from fastapi import APIRouter, HTTPException

from services.nexus.search import global_search

router = APIRouter()


@router.get("/")
def search(q: str, limit: int = 20):
    if not q or len(q.strip()) < 1:
        raise HTTPException(400, "Query parameter 'q' is required")
    return global_search(q.strip(), limit)
