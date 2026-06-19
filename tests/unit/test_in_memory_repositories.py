import asyncio
import unittest

from app.repositories.in_memory_vector_repository import InMemoryVectorRepository
from app.repositories.in_memory_video_repository import InMemoryVideoRepository


class TestInMemoryRepositories(unittest.TestCase):
    def test_video_repo_save_get_update(self):
        repo = InMemoryVideoRepository()
        video = {"id": "v1", "filename": "a.mp4", "status": "pending"}
        asyncio.run(repo.save(video))
        got = asyncio.run(repo.get_by_id("v1"))
        self.assertIsNotNone(got)
        self.assertEqual(got["filename"], "a.mp4")
        asyncio.run(repo.update_status("v1", "processing"))
        got2 = asyncio.run(repo.get_by_id("v1"))
        self.assertEqual(got2["status"], "processing")

    def test_vector_repo_upsert_and_search(self):
        repo = InMemoryVectorRepository()
        # simple vectors in 3D
        chunks = [
            {"id": "c1", "vector": [1.0, 0.0, 0.0], "payload": {"video_id": "v1", "text": "a", "start_seconds": 0.0}},
            {"id": "c2", "vector": [0.0, 1.0, 0.0], "payload": {"video_id": "v1", "text": "b", "start_seconds": 1.0}},
        ]
        asyncio.run(repo.upsert(chunks, "collection1"))
        # query near first vector
        results = asyncio.run(repo.search([1.0, 0.0, 0.0], "collection1", "v1", top_k=2))
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0].chunk_id, "c1")


if __name__ == '__main__':
    unittest.main()
