"""
VideoMind AI — Hybrid Retriever (Dense + Sparse BM25 Fusion)
=============================================================
Fuses dense vector scores with BM25 sparse scores using
Reciprocal Rank Fusion (RRF) or linear interpolation.

DESIGN PATTERN — Strategy:
    HybridRetriever composes a DenseRetriever and a BM25 retriever.
    The fusion function can be swapped (RRF vs. linear) without
    changing any caller.

SOLID — Interface Segregation:
    Implements IHybridRetriever. Dense-only callers use IDenseRetriever.
"""

from __future__ import annotations

from app.domain.entities import SearchResult
from app.domain.interfaces import IHybridRetriever

# Stub — implementation in Phase 7


class HybridRetriever(IHybridRetriever):
    """Fuses dense and BM25 sparse retrieval scores."""

    def search(
        self,
        query: str,
        query_vector: list[float],
        video_id: str,
        top_k: int = 10,
        alpha: float = 0.7,
    ) -> list[SearchResult]:
        raise NotImplementedError("Phase 7: Implement RRF hybrid fusion")
