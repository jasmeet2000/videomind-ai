import asyncio
import unittest
from unittest.mock import MagicMock

from app.domain.entities import TranscriptChunk
from app.repositories.in_memory_transcript_repository import InMemoryTranscriptRepository
from app.speech.whisper_service import WhisperService
from app.use_cases.ingest_video import IngestVideoUseCase
from app.video.processor import VideoProcessor


class TestIngestVideoUseCase(unittest.TestCase):
    def test_execute_calls_components_and_saves(self):
        video_processor = MagicMock(spec=VideoProcessor)
        video_processor.process.return_value = {"audio_path": "audio.wav", "metadata": {}}

        whisper_service = MagicMock(spec=WhisperService)
        chunks = [TranscriptChunk(video_id='v', text='a', start_seconds=0.0, end_seconds=1.0)]
        whisper_service.transcribe.return_value = chunks

        repo = InMemoryTranscriptRepository()

        usecase = IngestVideoUseCase(video_processor=video_processor, whisper_service=whisper_service, transcript_repo=repo)
        res = asyncio.run(usecase.execute("video.mp4", "v"))

        self.assertEqual(res["ingested_chunks"], 1)
        self.assertEqual(res["video_id"], "v")

        got = asyncio.run(repo.get_by_video_id("v"))
        self.assertEqual(len(got), 1)


if __name__ == '__main__':
    unittest.main()
