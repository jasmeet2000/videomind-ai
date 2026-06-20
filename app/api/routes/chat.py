"""
VideoMind AI — Chat API Route (Phase 9)
=========================================
RAG-based Q&A against a video.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.api.schemas.search import (
    ChatRequest,
    ChatResponse,
    SearchResultItem,
)
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_with_video(payload: ChatRequest, request: Request):
    """
    Answer a question about a video using RAG.
    """
    from app.api.dependencies.services import get_chat_use_case

    use_case = get_chat_use_case()

    if use_case is None:
        return ChatResponse(
            question=payload.question,
            answer="Chat pipeline is not configured. Please check server setup.",
            video_id=payload.video_id,
            sources=[],
            model_used=settings.ollama_model,
        )

    result = await use_case.execute(
        video_id=payload.video_id,
        query=payload.question,
    )

    sources = []
    for s in result.get("sources", []):
        start_m, start_s = divmod(int(s.get("start_seconds", 0)), 60)
        sources.append(
            SearchResultItem(
                chunk_id=s.get("chunk_id", ""),
                video_id=payload.video_id,
                modality=s.get("modality", "audio"),
                text=s.get("text", ""),
                score=s.get("score", 0.0),
                start_seconds=s.get("start_seconds", 0.0),
                end_seconds=s.get("end_seconds"),
                timestamp_label=f"{start_m:02d}:{start_s:02d}",
            )
        )

    return ChatResponse(
        question=payload.question,
        answer=result.get("answer", ""),
        video_id=payload.video_id,
        sources=sources,
        model_used=settings.ollama_model,
    )
