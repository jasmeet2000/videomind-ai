"""
Unit tests for repository adapters (VectorRepository delegation).
"""
import asyncio
import unittest

from app.domain.entities import SearchResult
from app.repositories.vector_repository import VectorRepository


class FakeAdapter:
    def __init__(self):
        self.upsert_called = False
        self.last_points = None
        self.last_collection = None

    async def upsert(self, points, collection=None):
        self.upsert_called = True
        self.last_points = points
        self.last_collection = collection

    async def search(self, vector, collection=None, video_id=None, top_k=10):
        # Return a deterministic SearchResult list
        return [
            SearchResult(
                chunk_id="c1",
                video_id=video_id or "v1",
                modality=None,
                text="hello",
                score=0.9,
                start_seconds=0.0,
                end_seconds=None,
                metadata={"video_id": video_id},
            )
        ]


class TestVectorRepository(unittest.TestCase):

    def test_upsert_delegates_and_converts(self):
        adapter = FakeAdapter()
        repo = VectorRepository(adapter)

        chunks = [
            {"id": "p1", "vector": [0.1, 0.2], "payload": {"video_id": "vid1", "text": "hello"}},
            {"id": "p2", "vector": [0.3, 0.4], "payload": {"video_id": "vid1", "text": "world"}},
        ]

        asyncio.run(repo.upsert(chunks, collection="col1"))

        self.assertTrue(adapter.upsert_called)
        self.assertEqual(adapter.last_collection, "col1")
        # Adapter should receive list of points with id/vector/payload
        self.assertIsInstance(adapter.last_points, list)
        self.assertEqual(len(adapter.last_points), 2)
        self.assertEqual(adapter.last_points[0]["id"], "p1")

    def test_search_delegates_and_returns_results(self):
        adapter = FakeAdapter()
        repo = VectorRepository(adapter)

        res = asyncio.run(repo.search([0.1, 0.2], collection="col1", video_id="vid1", top_k=5))
        self.assertIsInstance(res, list)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].video_id, "vid1")


if __name__ == "__main__":
    unittest.main()
