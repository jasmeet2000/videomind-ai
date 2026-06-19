import asyncio
import unittest

from app.domain.entities import TranscriptChunk
from app.repositories.in_memory_transcript_repository import InMemoryTranscriptRepository


class TestInMemoryTranscriptRepository(unittest.TestCase):
    def test_save_and_get(self):
        repo = InMemoryTranscriptRepository()
        chunks = [
            TranscriptChunk(video_id="vid1", text="hello", start_seconds=0.0, end_seconds=1.0, confidence=0.9),
            TranscriptChunk(video_id="vid1", text="world", start_seconds=1.0, end_seconds=2.0, confidence=0.8),
            TranscriptChunk(video_id="vid2", text="other", start_seconds=0.0, end_seconds=0.5, confidence=1.0),
        ]

        # Use asyncio.run to execute the coroutine in a synchronous test
        asyncio.run(repo.save_batch(chunks))

        fetched = asyncio.run(repo.get_by_video_id("vid1"))
        self.assertEqual(len(fetched), 2)
        self.assertEqual(fetched[0].text, "hello")
        self.assertEqual(fetched[1].text, "world")

        fetched2 = asyncio.run(repo.get_by_video_id("vid2"))
        self.assertEqual(len(fetched2), 1)
        self.assertEqual(fetched2[0].text, "other")


if __name__ == '__main__':
    unittest.main()
