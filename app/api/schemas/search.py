"""
VideoMind AI — Search & Chat API Schemas (Phase 2)
====================================================
Pydantic v2 request and response models for semantic search and RAG chat.

SOLID — Single Responsibility:
    Schemas validate shape only. Retrieval logic lives in use cases.

Production requirement:
    All inputs validated at the API boundary before reaching service layer.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.domain.entities import Modality

# ---------------------------------------------------------------------------
# Search schemas
# ---------------------------------------------------------------------------


class SearchRequest(BaseModel):
    """Natural language search query against a specific video."""

    query: str = Field(
        min_length=1,
        max_length=1000,
        description="Natural language search query (e.g., 'When did they discuss Docker?').",
    )
    video_id: str = Field(
        description="ID of the video to search within.",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of results to return (1–20).",
    )
    modality_filter: list[Modality] | None = Field(
        default=None,
        description="Restrict results to specific modalities (audio, visual, object, scene).",
    )


class SearchResultItem(BaseModel):
    """A single result from the semantic search pipeline."""

    chunk_id: str = Field(description="Unique ID of the retrieved chunk.")
    video_id: str = Field(description="Parent video identifier.")
    modality: Modality = Field(description="Pipeline that produced this chunk.")
    text: str = Field(description="Text content of the retrieved chunk.")
    score: float = Field(description="Relevance score [0.0, 1.0].")
    start_seconds: float = Field(description="Timestamp in the video (seconds).")
    end_seconds: float | None = Field(
        default=None,
        description="End timestamp for audio chunks; None for frame results.",
    )
    timestamp_label: str = Field(
        default="",
        description="Human-readable timestamp label (e.g., '04:32').",
    )


class SearchResponse(BaseModel):
    """Response containing ranked search results."""

    query: str
    video_id: str
    results: list[SearchResultItem]
    total_results: int = Field(description="Number of results returned.")


# ---------------------------------------------------------------------------
# Chat / RAG schemas
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    """Natural language question for RAG-based Q&A against a video."""

    question: str = Field(
        min_length=1,
        max_length=2000,
        description="User's natural language question about the video.",
    )
    video_id: str = Field(
        description="ID of the video to query.",
    )
    include_sources: bool = Field(
        default=True,
        description="If True, include the retrieved source chunks in the response.",
    )


class ChatResponse(BaseModel):
    """RAG-generated answer with optional source attribution."""

    question: str
    answer: str = Field(description="LLM-generated answer grounded in video content.")
    video_id: str
    sources: list[SearchResultItem] = Field(
        default_factory=list,
        description="Retrieved chunks used to generate the answer.",
    )
    model_used: str = Field(
        default="",
        description="Name of the LLM model that generated the answer.",
    )
