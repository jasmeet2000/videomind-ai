"""
VideoMind AI — Transcript Repository (PostgreSQL)
===================================================
Handles persistence of TranscriptChunk entities.

DESIGN PATTERN — Repository:
    Abstracts all SQL for transcript data. Supports batch inserts for
    efficiency (hundreds of chunks per video).
"""

from __future__ import annotations

from app.domain.entities import TranscriptChunk
from app.domain.interfaces import ITranscriptRepository

# Stub — implementation in Phase 6


class TranscriptRepository(ITranscriptRepository):
    """PostgreSQL-backed repository for TranscriptChunk persistence."""

    def __init__(self, db_session) -> None:
        self.db = db_session

    async def save_batch(self, chunks: list[TranscriptChunk]) -> None:
        raise NotImplementedError("Phase 6: Implement bulk INSERT with executemany")

    async def get_by_video_id(self, video_id: str) -> list[TranscriptChunk]:
        raise NotImplementedError("Phase 6: Implement SELECT WHERE video_id=...")
