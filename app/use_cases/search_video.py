"""
VideoMind AI — Use Case: Search Video
========================================
Handles semantic search queries against a video's indexed content.

Clean Architecture — Application Layer:
    Coordinates embedding the query, running hybrid retrieval, reranking,
    and returning results. No HTTP logic; no SQL.
"""

from __future__ import annotations

from app.domain.entities import SearchResult

# Stub — implementation in Phase 7


class SearchVideoUseCase:
    """Runs a natural language search query against a video's indexed chunks."""

    async def execute(
        self,
        query: str,
        video_id: str,
        top_k: int = 5,
    ) -> list[SearchResult]:
        """
        Embed the query, retrieve candidates, rerank, and return results.

        Args:
            query: Natural language search query from the user.
            video_id: Restrict search to this video.
            top_k: Number of results to return.

        Returns:
            List of SearchResult sorted by relevance.
        """
        raise NotImplementedError("Phase 7: Implement retrieval + reranking flow")
