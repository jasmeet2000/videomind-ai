import unittest

from app.embeddings.registry import ModelRegistry
from app.embeddings.service import EmbeddingService
import app.embeddings._default_models  # ensures fake model is registered
from app.core.exceptions import EmbeddingModelNotFoundError


class TestEmbeddings(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main()
