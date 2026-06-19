from __future__ import annotations

import hashlib
from typing import List

from app.domain.interfaces import IEmbeddingModel
from app.embeddings.registry import ModelRegistry


class FakeEmbeddingModel(IEmbeddingModel):
    """A tiny deterministic embedding model for tests and CI."""

    def __init__(self, dimension: int = 8, model_name: str = "fake") -> None:
        self._dim = dimension
        self._name = model_name

    def encode(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        vectors: List[List[float]] = []
        for t in texts:
            h = hashlib.sha256((t or "").encode("utf-8")).digest()
            vec = [float(b) / 255.0 for b in h[: self._dim]]
            vectors.append(vec)
        return vectors

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def model_name(self) -> str:
        return self._name


# Register the fake model under a friendly name so tests can use it.
ModelRegistry.register("fake", lambda: FakeEmbeddingModel())
