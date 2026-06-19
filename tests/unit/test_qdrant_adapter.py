"""
Unit tests for QdrantVectorRepository HTTP fallback behavior (mocked session).
"""
import asyncio
import unittest

from app.repositories.qdrant_vector_repository import QdrantVectorRepository
from app.domain.entities import SearchResult


class FakeResponse:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        return None

    def json(self):
        return self._data


class FakeSession:
    def __init__(self):
        self.put_called = False
        self.post_called = False
        self.last_put = None
        self.last_post = None

    def put(self, url, json=None, timeout=None):
        self.put_called = True
        self.last_put = {"url": url, "json": json}

    def post(self, url, json=None, timeout=None):
        self.post_called = True
        self.last_post = {"url": url, "json": json}
        return FakeResponse({"result": [{"id": "1", "payload": {"video_id": "v1", "text": "hi"}, "score": 0.9}]})


class TestQdrantAdapterHTTP(unittest.TestCase):

    def test_upsert_uses_http_put(self):
        repo = QdrantVectorRepository(host="localhost", port=6333, collection="col")
        repo._use_http = True
        repo._client = FakeSession()

        points = [{"id": "p1", "vector": [0.1, 0.2], "payload": {"video_id": "v1"}}]
        asyncio.run(repo.upsert(points, collection="col"))

        self.assertTrue(repo._client.put_called)
        self.assertIn("points", repo._client.last_put["json"])

    def test_search_uses_http_post_and_parses_results(self):
        repo = QdrantVectorRepository(host="localhost", port=6333, collection="col")
        repo._use_http = True
        repo._client = FakeSession()

        res = asyncio.run(repo.search([0.1, 0.2], collection="col", video_id="v1", top_k=5))
        self.assertIsInstance(res, list)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].video_id, "v1")


if __name__ == "__main__":
    unittest.main()
