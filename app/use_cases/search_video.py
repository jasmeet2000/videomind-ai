"""
VideoMind AI — Use Case: Search Video
========================================
Handles semantic search queries against a video's indexed content.

Clean Architecture — Application Layer:
    Coordinates embedding the query, running hybrid retrieval, reranking,
    and returning results. No HTTP logic; no SQL.
"""

from __future__ import annotations

from dataclasses import asdict
import logging

from app.domain.interfaces import IHybridRetriever, IReranker
from app.embeddings.service import EmbeddingService

logger = logging.getLogger(__name__)


class SearchVideoUseCase:
    """Runs a natural language search query against a video's indexed chunks."""

    def __init__(
        self,
        embedding_model: EmbeddingService,
        retriever: IHybridRetriever,
        reranker: IReranker,
    ) -> None:
        self.embedding_model = embedding_model
        self.retriever = retriever
        self.reranker = reranker

    async def execute(
        self,
        query: str,
        video_id: str,
        top_k: int = 5,
    ) -> list[dict]:
        """
        Embed the query, retrieve candidates, rerank, and return results.

        Args:
            query: Natural language search query from the user.
            video_id: Restrict search to this video.
            top_k: Number of results to return.

        Returns:
            List of result dicts sorted by relevance.
        """
        # Step 1: Encode the query into a dense vector
        logger.info("Encoding query: %s", query[:80])
        query_vectors = self.embedding_model.encode([query])
        if not query_vectors:
            logger.warning("Embedding returned empty vector for query")
            return []
        query_vector = query_vectors[0]

        # Step 2: Hybrid retrieval (dense + sparse fusion via RRF)
        logger.info("Running hybrid retrieval for video_id=%s", video_id)
        candidates = await self.retriever.search(
            query=query,
            query_vector=query_vector,
            video_id=video_id,
            top_k=top_k * 2,  # Fetch more candidates for reranking
        )

        if not candidates:
            logger.info("No candidates returned by retriever")
            return []

        # Step 3: Rerank using cross-encoder for precision
        logger.info("Reranking %d candidates", len(candidates))
        try:
            reranked = self.reranker.rerank(
                query=query,
                results=candidates,
                top_k=top_k,
            )
        except Exception as exc:
            # If reranker fails (e.g. model not installed), fall back to retriever order
            logger.warning("Reranker failed, using retriever order: %s", exc)
            reranked = candidates[:top_k]

        # Step 4: Convert SearchResult dataclasses to dicts for the route layer
        results = []
        for r in reranked:
            results.append(asdict(r))

        logger.info("Returning %d search results", len(results))
        return results
