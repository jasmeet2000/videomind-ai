"""
Unit tests for the Embedding Registry and EmbeddingService.

Tests register a FakeEmbeddingModel directly in the ModelRegistry
singleton to validate the factory/lookup/encode path without loading
any real sentence-transformer weights.
"""

import unittest

from app.core.exceptions import EmbeddingModelNotFoundError
from app.domain.interfaces import IEmbeddingModel
from app.embeddings.registry import _REGISTRY, ModelRegistry
from app.embeddings.service import EmbeddingService

_FAKE_DIM = 16


class FakeEmbeddingModel(IEmbeddingModel):
    """Minimal IEmbeddingModel for unit testing — no real weights."""

    def encode(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        return [[0.1] * _FAKE_DIM for _ in texts]

    @property
    def dimension(self) -> int:
        return _FAKE_DIM

    @property
    def model_name(self) -> str:
        return "fake"


class TestEmbeddings(unittest.TestCase):
    def setUp(self):
        """Register the fake model and clear any cached instance."""
        ModelRegistry.register("fake", FakeEmbeddingModel)
        ModelRegistry._loaded_models.clear()

    def tearDown(self):
        """Remove test registration and cached models to keep registry clean."""
        _REGISTRY.pop("fake", None)
        ModelRegistry._loaded_models.clear()

    def test_registry_missing_model_raises(self):
        reg = ModelRegistry.get_instance()
        with self.assertRaises(EmbeddingModelNotFoundError):
            reg.get_model("this-model-does-not-exist")

    def test_fake_model_encode_and_service(self):
        reg = ModelRegistry.get_instance()
        model = reg.get_model("fake")
        svc = EmbeddingService(model)
        texts = ["hello world", "the quick brown fox"]
        vecs = svc.encode(texts)
        self.assertEqual(len(vecs), 2)
        self.assertEqual(len(vecs[0]), model.dimension)

    def test_registry_caches_model_instance(self):
        """get_model returns the same cached object on repeated calls."""
        reg = ModelRegistry.get_instance()
        m1 = reg.get_model("fake")
        m2 = reg.get_model("fake")
        self.assertIs(m1, m2)

    def test_service_empty_input(self):
        """EmbeddingService.encode([]) returns an empty list."""
        reg = ModelRegistry.get_instance()
        model = reg.get_model("fake")
        svc = EmbeddingService(model)
        self.assertEqual(svc.encode([]), [])

    def test_service_dimension_property(self):
        """EmbeddingService.dimension proxies the model dimension."""
        reg = ModelRegistry.get_instance()
        model = reg.get_model("fake")
        svc = EmbeddingService(model)
        self.assertEqual(svc.dimension, _FAKE_DIM)


if __name__ == "__main__":
    unittest.main()
