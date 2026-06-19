import unittest

from app.domain.entities import TranscriptChunk
from app.speech.chunker import chunk_transcript_chunks


class TestChunker(unittest.TestCase):
    def test_empty_segments(self):
        self.assertEqual(chunk_transcript_chunks([]), [])

    def test_basic_grouping_without_overlap(self):
        # token_counter returns 1 token per segment for deterministic behavior
        segments = [
            TranscriptChunk(video_id="v", text="a", start_seconds=0.0, end_seconds=0.5, confidence=1.0),
            TranscriptChunk(video_id="v", text="b", start_seconds=1.0, end_seconds=1.5, confidence=1.0),
            TranscriptChunk(video_id="v", text="c", start_seconds=2.0, end_seconds=2.5, confidence=1.0),
            TranscriptChunk(video_id="v", text="d", start_seconds=3.0, end_seconds=3.5, confidence=1.0),
        ]
        chunks = chunk_transcript_chunks(segments, max_tokens=2, overlap_tokens=0, token_counter=lambda t: 1)
        # With max_tokens=2 and each segment=1 token, expect 2 chunks (2 segments each)
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0].start_seconds, 0.0)
        self.assertEqual(chunks[0].end_seconds, 1.5)
        self.assertEqual(chunks[1].start_seconds, 2.0)

    def test_overlap_behaviour(self):
        segments = [
            TranscriptChunk(video_id="v", text="a", start_seconds=0.0, end_seconds=0.5, confidence=1.0),
            TranscriptChunk(video_id="v", text="b", start_seconds=1.0, end_seconds=1.5, confidence=1.0),
            TranscriptChunk(video_id="v", text="c", start_seconds=2.0, end_seconds=2.5, confidence=1.0),
            TranscriptChunk(video_id="v", text="d", start_seconds=3.0, end_seconds=3.5, confidence=1.0),
        ]
        chunks = chunk_transcript_chunks(segments, max_tokens=2, overlap_tokens=1, token_counter=lambda t: 1)
        # With overlap=1 and 4 segments, expected chunk sequence: [0-1], [1-2], [2-3] => 3 chunks
        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0].start_seconds, 0.0)
        self.assertEqual(chunks[1].start_seconds, 1.0)
        self.assertEqual(chunks[2].start_seconds, 2.0)


if __name__ == '__main__':
    unittest.main()
