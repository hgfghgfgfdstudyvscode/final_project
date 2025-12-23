from __future__ import annotations
from fastapi import APIRouter, Query

from services.search_service import SearchService

router = APIRouter()
service = SearchService()


@router.get("/search")
def search(
    query: str | None = Query(None, min_length=2),
    q: str | None = Query(None, min_length=2),
):
    raw_query = (query or q or "").strip()
    return service.search(raw_query)
