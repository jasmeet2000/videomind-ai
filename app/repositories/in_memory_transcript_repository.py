"""In-memory transcript repository for testing and simple local runs.

This repository implements the ITranscriptRepository interface and stores
TranscriptChunk instances in an in-memory dictionary keyed by video_id.
"""

from __future__ import annotations

from typing import Dict, List

from app.domain.entities import TranscriptChunk
from app.domain.interfaces import ITranscriptRepository


class InMemoryTranscriptRepository(ITranscriptRepository):
    """Simple in-memory repository for TranscriptChunk objects."""

    def __init__(self) -> None:
        self._store: Dict[str, List[TranscriptChunk]] = {}

    async def save_batch(self, chunks: list[TranscriptChunk]) -> None:
        """Persist a batch of TranscriptChunk objects in memory.

        This appends chunks to the list for their video_id preserving order.
        """
        for c in chunks:
            self._store.setdefault(c.video_id, []).append(c)

    async def get_by_video_id(self, video_id: str) -> list[TranscriptChunk]:
        """Retrieve all chunks for a given video_id (empty list if none)."""
        return list(self._store.get(video_id, []))
