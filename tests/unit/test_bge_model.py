"""
Unit test for BGEEmbeddingModel using a fake SentenceTransformer.
"""
import unittest

import numpy as np

import app.embeddings.bge_model as bge_module


class FakeST:
    def __init__(self, name, device=None):
        self._name = name

    def encode(self, texts, batch_size=32, convert_to_numpy=True, show_progress_bar=False):
        return np.array([[0.1] * 384 for _ in texts])

    def get_sentence_embedding_dimension(self):
        return 384


class TestBGEModel(unittest.TestCase):

    def test_encode_with_fake_sentence_transformer(self):
        orig = getattr(bge_module, "SentenceTransformer", None)
        try:
            bge_module.SentenceTransformer = FakeST
            m = bge_module.BGEEmbeddingModel()
            vecs = m.encode(["hello", "world"], batch_size=2)
            self.assertEqual(len(vecs), 2)
            self.assertEqual(len(vecs[0]), 384)
            self.assertEqual(m.dimension, 384)
        finally:
            if orig is not None:
                bge_module.SentenceTransformer = orig


if __name__ == "__main__":
    unittest.main()
