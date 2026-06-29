from fastapi import APIRouter, Query

from app.schemas.paper import PaperResult
from app.services.paper_service import search_all_sources

router = APIRouter(prefix="/papers", tags=["Papers"])


@router.get("", response_model=list[PaperResult])
async def search_papers(
    keyword: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    results = await search_all_sources(keyword, page, page_size)
    return results[:page_size]
