from __future__ import annotations

from typing import Any

from app.domain.interfaces import IVideoRepository


class InMemoryVideoRepository(IVideoRepository):
    """In-memory video metadata repository for tests and CI."""

    def __init__(self) -> None:
        # video_id -> dict
        self._store: dict[str, dict[str, Any]] = {}

    async def save(self, video: dict[str, Any]) -> None:
        self._store[video.get("id")] = video.copy()

    async def get_by_id(self, video_id: str) -> dict[str, Any] | None:
        return self._store.get(video_id)

    async def update_status(self, video_id: str, status: str) -> None:
        if video_id in self._store:
            self._store[video_id]["status"] = status
