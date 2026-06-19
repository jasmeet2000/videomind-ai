"""
VideoMind AI — Use Case: Ingest Video
=======================================
Orchestrates the full ingestion pipeline for a single uploaded video.

SOLID — Single Responsibility:
    This use case coordinates other services. It does NOT implement
    audio extraction, transcription, OCR, or embedding logic itself.

SOLID — Dependency Inversion:
    All dependencies (services, repos) are injected via constructor.
    No service is instantiated inside this class.

Clean Architecture — Application Layer:
    This is the highest layer that contains business logic. It calls
    service-layer classes and repository interfaces.
    It never handles HTTP requests or response formatting.
"""

from __future__ import annotations

from __future__ import annotations

from typing import Any, Dict

from app.video.processor import VideoProcessor
from app.speech.whisper_service import WhisperService
from app.repositories.in_memory_transcript_repository import InMemoryTranscriptRepository
from app.domain.interfaces import ITranscriptRepository, IVideoRepository
from app.core.logging import get_logger

logger = get_logger(__name__)


class IngestVideoUseCase:
    """Orchestrates the full ingestion pipeline for a single uploaded video.

    This implementation is a lightweight, testable orchestrator used during
    Phase 4-6 development. It composes VideoProcessor, WhisperService, and
    a TranscriptRepository to produce and persist transcript chunks.
    """

    def __init__(
        self,
        video_processor: VideoProcessor | None = None,
        whisper_service: WhisperService | None = None,
        transcript_repo: ITranscriptRepository | None = None,
        video_repo: IVideoRepository | None = None,
    ) -> None:
        self.video_processor = video_processor or VideoProcessor()
        self.whisper_service = whisper_service or WhisperService()
        self.transcript_repo = transcript_repo or InMemoryTranscriptRepository()
        self.video_repo = video_repo

    async def execute(self, video_path: str, video_id: str) -> Dict[str, Any]:
        """Run metadata, audio extraction, transcription, and persist chunks.

        Returns a summary dict with counts and metadata.
        """
        summary = self.video_processor.process(video_path, video_id)
        audio_path = summary.get("audio_path")

        transcripts = self.whisper_service.transcribe(audio_path, video_id)

        await self.transcript_repo.save_batch(transcripts)

        if self.video_repo is not None:
            # Save basic metadata for downstream services (may be a no-op in tests)
            meta = {
                "id": video_id,
                "source_uri": video_path,
                "duration_seconds": (summary.get("metadata") or {}).get("duration_seconds"),
            }
            await self.video_repo.save(meta)

        return {
            "video_id": video_id,
            "ingested_chunks": len(transcripts),
            "metadata": summary.get("metadata"),
        }
