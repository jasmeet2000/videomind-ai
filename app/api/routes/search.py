"""
VideoMind AI — Search API Route (Phase 9)
============================================
Semantic search across a video's indexed content.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.api.schemas.search import (
    SearchRequest,
    SearchResponse,
    SearchResultItem,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search_video(payload: SearchRequest, request: Request):
    """
    Perform hybrid semantic search across a video's indexed content.
    """
    from app.api.dependencies.services import get_search_use_case

    use_case = get_search_use_case()

    if use_case is None:
        # Fallback: return empty results if search pipeline is not wired
        return SearchResponse(
            query=payload.query,
            video_id=payload.video_id,
            results=[],
            total_results=0,
        )

    results = await use_case.execute(
        video_id=payload.video_id,
        query=payload.query,
        top_k=payload.top_k,
    )

    items = []
    for r in results:
        start_m, start_s = divmod(int(r.get("start_seconds", 0)), 60)
        items.append(SearchResultItem(
            chunk_id=r.get("chunk_id", ""),
            video_id=r.get("video_id", payload.video_id),
            modality=r.get("modality", "audio"),
            text=r.get("text", ""),
            score=r.get("score", 0.0),
            start_seconds=r.get("start_seconds", 0.0),
            end_seconds=r.get("end_seconds"),
            timestamp_label=f"{start_m:02d}:{start_s:02d}",
        ))

    return SearchResponse(
        query=payload.query,
        video_id=payload.video_id,
        results=items,
        total_results=len(items),
    )
