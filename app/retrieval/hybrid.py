"""
VideoMind AI — Hybrid Retriever (Dense + Sparse BM25 Fusion)
=============================================================
Fuses dense vector scores with BM25 sparse scores using
Reciprocal Rank Fusion (RRF).

DESIGN PATTERN — Strategy:
    HybridRetriever composes a DenseRetriever and a BM25 retriever.
    The fusion function can be swapped without changing any caller.

SOLID — Interface Segregation:
    Implements IHybridRetriever. Dense-only callers use IDenseRetriever.
"""

from __future__ import annotations

import asyncio
from typing import Dict

from app.domain.entities import SearchResult
from app.domain.interfaces import IDenseRetriever, IHybridRetriever, ISparseRetriever


class HybridRetriever(IHybridRetriever):
    """Fuses dense and BM25 sparse retrieval scores using RRF."""

    def __init__(
        self,
        dense_retriever: IDenseRetriever,
        sparse_retriever: ISparseRetriever,
        rrf_k: int = 60,
    ) -> None:
        self.dense_retriever = dense_retriever
        self.sparse_retriever = sparse_retriever
        self.rrf_k = rrf_k

    async def search(
        self,
        query: str,
        query_vector: list[float],
        video_id: str,
        top_k: int = 10,
        alpha: float = 0.7,
    ) -> list[SearchResult]:
        """
        Fuse dense and sparse scores using Reciprocal Rank Fusion.
        """
        # Execute dense and sparse retrieval concurrently
        dense_results, sparse_results = await asyncio.gather(
            self.dense_retriever.search(query_vector=query_vector, video_id=video_id, top_k=top_k * 2),
            self.sparse_retriever.search(query=query, video_id=video_id, top_k=top_k * 2),
        )

        fused_scores: Dict[str, float] = {}
        chunks_map: Dict[str, SearchResult] = {}

        # Apply Reciprocal Rank Fusion (RRF)
        # RRF_score = sum( 1 / (k + rank) )

        for rank, res in enumerate(dense_results, start=1):
            if res.chunk_id not in fused_scores:
                fused_scores[res.chunk_id] = 0.0
                chunks_map[res.chunk_id] = res
            fused_scores[res.chunk_id] += 1.0 / (self.rrf_k + rank)

        for rank, res in enumerate(sparse_results, start=1):
            if res.chunk_id not in fused_scores:
                fused_scores[res.chunk_id] = 0.0
                chunks_map[res.chunk_id] = res
            fused_scores[res.chunk_id] += 1.0 / (self.rrf_k + rank)

        # Update scores in the SearchResult objects
        fused_results = []
        for chunk_id, score in fused_scores.items():
            res = chunks_map[chunk_id]
            # Replace score with fused RRF score
            fused_results.append(
                SearchResult(
                    chunk_id=res.chunk_id,
                    video_id=res.video_id,
                    modality=res.modality,
                    text=res.text,
                    score=score,
                    start_seconds=res.start_seconds,
                    end_seconds=res.end_seconds,
                    metadata=res.metadata,
                )
            )

        # Sort descending by fused score
        fused_results.sort(key=lambda x: x.score, reverse=True)
        return fused_results[:top_k]
