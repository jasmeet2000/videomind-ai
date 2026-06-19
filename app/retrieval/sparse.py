"""
VideoMind AI — Sparse Retriever
=================================
Performs sparse (BM25) search by fetching transcript chunks and scoring them locally.
"""

from __future__ import annotations

import logging

from app.domain.entities import SearchResult
from app.domain.interfaces import ISparseRetriever, ITranscriptRepository

logger = logging.getLogger(__name__)

try:
    from rank_bm25 import BM25Plus
except ImportError:
    BM25Plus = None


class BM25SparseRetriever(ISparseRetriever):
    """
    Performs BM25 search over a single video's transcripts in-memory.
    This is highly efficient for single-video scopes since the chunk count is small.
    """

    def __init__(self, transcript_repo: ITranscriptRepository) -> None:
        self.transcript_repo = transcript_repo

    async def search(
        self,
        query: str,
        video_id: str,
        top_k: int = 10,
    ) -> list[SearchResult]:
        """
        Search using BM25 term-frequency scoring.
        """
        if BM25Plus is None:
            logger.error("rank_bm25 is not installed. Sparse retrieval returning empty.")
            return []

        chunks = await self.transcript_repo.get_by_video_id(video_id)
        if not chunks:
            return []

        # Tokenize chunks
        tokenized_corpus = [chunk.text.lower().split() for chunk in chunks]
        bm25 = BM25Plus(tokenized_corpus)

        # Tokenize query
        tokenized_query = query.lower().split()

        # Get scores
        scores = bm25.get_scores(tokenized_query)

        results = []
        for i, chunk in enumerate(chunks):
            # Only include chunks that actually contain at least one query term
            has_match = any(term in tokenized_corpus[i] for term in tokenized_query)
            if has_match:
                results.append(
                    SearchResult(
                        chunk_id=chunk.id,
                        video_id=chunk.video_id,
                        modality="speech",
                        text=chunk.text,
                        score=float(scores[i]),
                        start_seconds=chunk.start_seconds,
                        end_seconds=chunk.end_seconds,
                        metadata={},
                    )
                )

        # Sort by score descending and take top_k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
