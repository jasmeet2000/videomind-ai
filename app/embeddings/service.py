"""
VideoMind AI — Embedding Service
==================================
Encodes text into dense vectors using the configured IEmbeddingModel.

SOLID — Dependency Inversion:
    EmbeddingService depends on IEmbeddingModel (abstract), not on
    BAAI/bge-small or any concrete model. Swap models by changing
    which IEmbeddingModel is injected.

SOLID — Single Responsibility:
    Only encodes text to vectors. Does not store vectors or retrieve them.
"""

from __future__ import annotations

from app.domain.interfaces import IEmbeddingModel

# Stub — implementation in Phase 6


class EmbeddingService:
    """
    Encodes text strings into dense float vectors.

    DESIGN PATTERN — Dependency Injection:
        The IEmbeddingModel implementation is injected at construction.
        This enables unit testing with a mock model.
    """

    def __init__(self, model: IEmbeddingModel) -> None:
        """
        Args:
            model: An IEmbeddingModel implementation (e.g., BGEModel).
        """
        self.model = model

    def encode(self, texts: list[str]) -> list[list[float]]:
        """
        Encode a list of texts into embedding vectors.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of float vectors, one per input text.
        """
        # Delegate to the injected embedding model
        if not texts:
            return []
        return self.model.encode(texts)


    @property
    def dimension(self) -> int:
        """Return the dimensionality of the embedding model's output vectors."""
        return self.model.dimension
