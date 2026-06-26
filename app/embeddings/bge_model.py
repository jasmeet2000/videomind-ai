"""
BGE Embedding Model adapter for VideoMind AI

Implements IEmbeddingModel using the sentence-transformers wrapper for
BAAI/bge-small-en-v1.5. Loads lazily and runs on CPU by default.

PERFORMANCE — Lazy Imports & Batch Sizing:
    The heavy sentence-transformers module is imported lazily inside
    _ensure_model() to prevent a 2-second import penalty at startup.
    Default batch size is reduced to 16 to minimize peak RAM usage on CPU.
"""

from __future__ import annotations

import numpy as np

from app.domain.interfaces import IEmbeddingModel
from app.embeddings.registry import ModelRegistry


class BGEEmbeddingModel(IEmbeddingModel):
    """Adapter around SentenceTransformer for the BGE model.

    Loads the model lazily to avoid expensive startup costs during import.
    """

    DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"

    def __init__(self, model_name: str | None = None) -> None:
        self._model_name = model_name or self.DEFAULT_MODEL
        self._model = None

    def _ensure_model(self) -> None:
        if self._model is not None:
            return
        
        # Lazy import of heavy ML library
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise RuntimeError("sentence-transformers package is required for BGEEmbeddingModel")
            
        # Force CPU-only inference
        self._model = SentenceTransformer(self._model_name, device="cpu")

    def encode(self, texts: list[str], batch_size: int = 16) -> list[list[float]]:
        """Encode texts into dense vectors (lists of floats).

        Args:
            texts: list of input strings
            batch_size: batch size for the underlying model. Reduced to 16 for CPU memory safety.

        Returns:
            List of embedding vectors (one per input text)
        """
        if not texts:
            return []
        self._ensure_model()
        # sentence-transformers can return numpy arrays when convert_to_numpy=True
        embeddings = self._model.encode(
            texts, batch_size=batch_size, convert_to_numpy=True, show_progress_bar=False
        )
        # Ensure a 2D numpy array
        if isinstance(embeddings, np.ndarray):
            return [row.tolist() for row in embeddings]
        # Fallback — coerce element-wise
        return [list(map(float, v)) for v in embeddings]

    @property
    def dimension(self) -> int:
        if self._model is not None:
            try:
                return int(self._model.get_sentence_embedding_dimension())
            except Exception:
                return 384
        return 384

    @property
    def model_name(self) -> str:
        return self._model_name


# Register the model in the central registry so callers can request it by name
try:
    ModelRegistry.register(BGEEmbeddingModel.DEFAULT_MODEL, BGEEmbeddingModel)
except Exception:
    # Registration is best-effort during import; keep import-time side-effects minimal
    pass
