"""
VideoMind AI — Domain Interfaces (Abstract Base Classes)
=========================================================
Defines the contracts that all service implementations must satisfy.

SOLID Principle — Dependency Inversion (DIP):
    Higher-level layers (use cases, API) depend on these abstractions,
    NOT on concrete implementations (PaddleOCR, Whisper, Qdrant client).
    This means swapping any implementation requires zero changes upstream.

SOLID Principle — Interface Segregation (ISP):
    Retrieval interfaces are deliberately split into IDenseRetriever,
    ISparseRetriever, and IHybridRetriever. No class is forced to
    implement methods it doesn't need.

SOLID Principle — Liskov Substitution (LSP):
    Any concrete implementation of IOCREngine can replace any other —
    the caller receives the same List[TextBlock] regardless of engine.

Layer rule: This file may ONLY import from stdlib, third-party, and
            app.domain.entities. Never import from service layers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np

from app.domain.entities import SearchResult, TextBlock, TranscriptChunk

# ---------------------------------------------------------------------------
# OCR Engine Interface
# DESIGN PATTERN — Strategy: OCRService holds a reference to IOCREngine
#   and delegates extraction to whichever concrete engine is selected at
#   runtime (PaddleOCR or EasyOCR). The caller is unaware of which ran.
# DESIGN PATTERN — Adapter: PaddleOCRAdapter and EasyOCRAdapter wrap the
#   external libraries' incompatible APIs into this unified contract.
# ---------------------------------------------------------------------------

class IOCREngine(ABC):
    """Contract for all OCR engine implementations."""

    @abstractmethod
    def extract(self, image: np.ndarray) -> list[TextBlock]:
        """
        Extract text blocks from an image array.

        Args:
            image: BGR image array as returned by OpenCV (H x W x 3).

        Returns:
            List of TextBlock instances with text, confidence, and bounding box.
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the engine's dependencies are installed and ready."""
        ...


# ---------------------------------------------------------------------------
# Embedding Model Interface
# DESIGN PATTERN — Open/Closed: The EmbeddingService is open to new models
#   (register in ModelRegistry) but closed to modification. New models
#   implement IEmbeddingModel; no existing code changes.
# ---------------------------------------------------------------------------

class IEmbeddingModel(ABC):
    """Contract for all embedding model implementations."""

    @abstractmethod
    def encode(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """
        Encode a list of text strings into dense vectors.

        Args:
            texts: List of strings to embed.
            batch_size: Number of texts to process per forward pass.

        Returns:
            List of embedding vectors (each a list of floats).
        """
        ...

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the dimensionality of the output vectors."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the HuggingFace model identifier."""
        ...


# ---------------------------------------------------------------------------
# LLM Backend Interface
# DESIGN PATTERN — Strategy: LLMService selects a backend at startup based
#   on config. Qwen3, Llama 3.1, and Gemma 3 are interchangeable.
# ---------------------------------------------------------------------------

class ILLMBackend(ABC):
    """Contract for all LLM backend implementations."""

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> str:
        """
        Generate a text response for a given prompt.

        Args:
            prompt: The fully assembled prompt string.
            **kwargs: Backend-specific options (temperature, max_tokens, etc.).

        Returns:
            The generated text response as a string.
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the LLM backend is reachable."""
        ...


# ---------------------------------------------------------------------------
# Retrieval Interfaces
# SOLID — Interface Segregation (ISP):
#   Dense, sparse, and hybrid retrieval have separate interfaces.
#   A dense-only implementation is not forced to implement sparse methods.
# ---------------------------------------------------------------------------

class IDenseRetriever(ABC):
    """Contract for dense (vector similarity) retrieval."""

    @abstractmethod
    async def search(
        self,
        query_vector: list[float],
        video_id: str,
        top_k: int = 10,
    ) -> list[SearchResult]:
        """
        Search for the top-k most similar chunks by vector similarity.

        Args:
            query_vector: Dense embedding of the query text.
            video_id: Restrict search to this video's chunks.
            top_k: Maximum number of results to return.

        Returns:
            List of SearchResult sorted by descending score.
        """
        ...


class ISparseRetriever(ABC):
    """Contract for sparse (keyword / BM25) retrieval."""

    @abstractmethod
    async def search(
        self,
        query: str,
        video_id: str,
        top_k: int = 10,
    ) -> list[SearchResult]:
        """
        Search using BM25 term-frequency scoring.

        Args:
            query: Raw query text string.
            video_id: Restrict search to this video's chunks.
            top_k: Maximum number of results to return.

        Returns:
            List of SearchResult sorted by descending BM25 score.
        """
        ...


class IHybridRetriever(ABC):
    """Contract for hybrid (dense + sparse fusion) retrieval."""

    @abstractmethod
    async def search(
        self,
        query: str,
        query_vector: list[float],
        video_id: str,
        top_k: int = 10,
        alpha: float = 0.7,
    ) -> list[SearchResult]:
        """
        Fuse dense and sparse scores using Reciprocal Rank Fusion or linear combo.

        Args:
            query: Raw query text (for sparse scoring).
            query_vector: Dense embedding (for vector scoring).
            video_id: Restrict search to this video's chunks.
            top_k: Maximum results to return.
            alpha: Weight for dense score (1-alpha goes to sparse).

        Returns:
            List of SearchResult sorted by fused score.
        """
        ...


# ---------------------------------------------------------------------------
# Reranker Interface
# ---------------------------------------------------------------------------

class IReranker(ABC):
    """Contract for cross-encoder reranking of retrieved results."""

    @abstractmethod
    def rerank(
        self,
        query: str,
        results: list[SearchResult],
        top_k: int = 5,
    ) -> list[SearchResult]:
        """
        Re-score and re-rank results using a cross-encoder model.

        Args:
            query: Original user query.
            results: Candidate results from the retriever.
            top_k: Number of results to return after reranking.

        Returns:
            Top-k results sorted by cross-encoder relevance score.
        """
        ...


# ---------------------------------------------------------------------------
# Video Repository Interface
# DESIGN PATTERN — Repository: Abstracts all persistence operations.
#   Use cases call these methods; they never execute SQL directly.
# ---------------------------------------------------------------------------

class IVideoRepository(ABC):
    """Contract for video metadata persistence."""

    @abstractmethod
    async def save(self, video: Any) -> None:
        """Persist a new Video entity."""
        ...

    @abstractmethod
    async def get_by_id(self, video_id: str) -> Any | None:
        """Retrieve a Video by its ID, or None if not found."""
        ...

    @abstractmethod
    async def update_status(self, video_id: str, status: str) -> None:
        """Update the processing status of a video."""
        ...


class ITranscriptRepository(ABC):
    """Contract for transcript chunk persistence."""

    @abstractmethod
    async def save_batch(self, chunks: list[TranscriptChunk]) -> None:
        """Persist a batch of transcript chunks for a video."""
        ...

    @abstractmethod
    async def get_by_video_id(self, video_id: str) -> list[TranscriptChunk]:
        """Retrieve all chunks for a given video."""
        ...


class IVectorRepository(ABC):
    """Contract for vector database operations (Qdrant)."""

    @abstractmethod
    async def upsert(
        self,
        chunks: list[dict[str, Any]],
        collection: str,
    ) -> None:
        """
        Upsert a batch of point dicts (id, vector, payload) into Qdrant.

        Args:
            chunks: List of {'id': str, 'vector': list[float], 'payload': dict}.
            collection: Qdrant collection name.
        """
        ...

    @abstractmethod
    async def search(
        self,
        query_vector: list[float],
        collection: str,
        video_id: str,
        top_k: int,
    ) -> list[SearchResult]:
        """Search the vector collection and return scored results."""
        ...
