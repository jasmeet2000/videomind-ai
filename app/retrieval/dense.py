"""
VideoMind AI — Dense Retriever
================================
Performs dense vector similarity search against Qdrant.

SOLID — Interface Segregation:
    Implements IDenseRetriever only. Hybrid fusion is in hybrid.py.

DESIGN PATTERN — Repository:
    DenseRetriever wraps IVectorRepository (the Qdrant client abstraction).
    Business logic (top_k, score thresholds) lives here, not in the repo.
"""

from __future__ import annotations

from app.domain.entities import SearchResult
from app.domain.interfaces import IDenseRetriever, IVectorRepository

# Stub — implementation in Phase 7


class DenseRetriever(IDenseRetriever):
    """Performs ANN (approximate nearest-neighbor) search via Qdrant."""

    def __init__(self, vector_repo: IVectorRepository, collection: str) -> None:
        self.vector_repo = vector_repo
        self.collection = collection

    def search(
        self,
        query_vector: list[float],
        video_id: str,
        top_k: int = 10,
    ) -> list[SearchResult]:
        raise NotImplementedError("Phase 7: Implement Qdrant dense search")
