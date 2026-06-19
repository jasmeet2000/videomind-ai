"""
VideoMind AI — Vector Repository (Qdrant)
==========================================
Handles all upsert and search operations against Qdrant collections.

DESIGN PATTERN — Repository:
    Wraps the qdrant-client. Use cases and retrievers call upsert()/search()
    without knowing any Qdrant-specific API details.

DESIGN PATTERN — Singleton:
    The Qdrant client is expensive to instantiate. It is created once
    and injected here via dependency injection.
"""

from __future__ import annotations

from typing import Any

from app.domain.entities import SearchResult
from app.domain.interfaces import IVectorRepository

# Stub — implementation in Phase 6


class VectorRepository(IVectorRepository):
    """Qdrant-backed repository for vector upsert and similarity search."""

    def __init__(self, qdrant_client) -> None:
        self.client = qdrant_client

    async def upsert(
        self,
        chunks: list[dict[str, Any]],
        collection: str,
    ) -> None:
        raise NotImplementedError("Phase 6: Implement Qdrant batch upsert")

    async def search(
        self,
        query_vector: list[float],
        collection: str,
        video_id: str,
        top_k: int,
    ) -> list[SearchResult]:
        raise NotImplementedError("Phase 6: Implement Qdrant ANN search with filter")
