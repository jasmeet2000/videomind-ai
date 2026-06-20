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

    def __init__(self, qdrant_adapter) -> None:
        """qdrant_adapter should implement the async methods `upsert(points, collection)` and `search(vector, collection, video_id, top_k)`.

        Typically this is an instance of QdrantVectorRepository.
        """
        self._adapter = qdrant_adapter

    async def upsert(
        self,
        chunks: list[dict[str, Any]],
        collection: str,
    ) -> None:
        """Convert incoming chunk dicts to Qdrant point format and delegate to adapter."""
        points = []
        for c in chunks:
            # Expecting each chunk dict to contain 'id', 'vector', and 'payload'
            pid = c.get("id")
            vec = c.get("vector")
            payload = c.get("payload", {}) or {}
            points.append({"id": pid, "vector": vec, "payload": payload})

        await self._adapter.upsert(points, collection=collection)

    async def search(
        self,
        query_vector: list[float],
        collection: str,
        video_id: str,
        top_k: int,
    ) -> list[SearchResult]:
        """Delegate search to the underlying Qdrant adapter, supplying video_id for filtering."""
        return await self._adapter.search(
            query_vector, collection=collection, video_id=video_id, top_k=top_k
        )
