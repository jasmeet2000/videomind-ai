"""
VideoMind AI — Cross-Encoder Reranker
=======================================
Re-scores retrieved results using a cross-encoder model that jointly
encodes the query and each candidate passage for higher accuracy.

SOLID — Single Responsibility:
    Only reranks. Retrieval is in dense.py and hybrid.py.

DESIGN PATTERN — Strategy:
    Reranker can be swapped (cross-encoder model, GPT4All rerank, etc.)
    by implementing IReranker. Callers don't change.
"""

from __future__ import annotations

import logging

from app.domain.entities import SearchResult
from app.domain.interfaces import IReranker

logger = logging.getLogger(__name__)


class CrossEncoderReranker(IReranker):
    """Reranks results with a cross-encoder model for precision."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2") -> None:
        self.model_name = model_name
        self._model = None  # Lazy-loaded

    def _ensure_model(self) -> None:
        """Lazily load the cross-encoder model."""
        if self._model is not None:
            return
        try:
            from sentence_transformers import CrossEncoder

            logger.info(f"Loading CrossEncoder: {self.model_name} on CPU...")
            self._model = CrossEncoder(self.model_name, device="cpu")
            logger.info("CrossEncoder loaded successfully.")
        except ImportError as e:
            logger.error("sentence-transformers is not installed. CrossEncoderReranker cannot run.")
            raise RuntimeError("sentence-transformers not installed") from e
        except Exception as e:
            logger.error(f"Failed to load CrossEncoder: {e}")
            raise

    def rerank(
        self,
        query: str,
        results: list[SearchResult],
        top_k: int = 5,
    ) -> list[SearchResult]:
        """
        Re-score and re-rank results using a cross-encoder model.
        """
        if not results:
            return []

        self._ensure_model()

        # Format input pairs for the cross-encoder: [(query, passage1), (query, passage2), ...]
        cross_inp = [[query, res.text] for res in results]

        # Get logits (scores)
        scores = self._model.predict(cross_inp)

        reranked_results = []
        for i, res in enumerate(results):
            # Update the score with the cross-encoder score
            reranked_results.append(
                SearchResult(
                    chunk_id=res.chunk_id,
                    video_id=res.video_id,
                    modality=res.modality,
                    text=res.text,
                    score=float(scores[i]),
                    start_seconds=res.start_seconds,
                    end_seconds=res.end_seconds,
                    metadata=res.metadata,
                )
            )

        # Sort descending by cross-encoder score
        reranked_results.sort(key=lambda x: x.score, reverse=True)
        return reranked_results[:top_k]
