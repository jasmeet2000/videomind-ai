"""
VideoMind AI — Video Repository (PostgreSQL)
==============================================
Handles all persistence operations for Video entities.

DESIGN PATTERN — Repository:
    All SQL lives in this class. Use cases call repository methods —
    they never write SQL or know about asyncpg/SQLAlchemy internals.

SOLID — Dependency Inversion:
    VideoRepository implements IVideoRepository. Use cases depend on
    the interface, not this concrete class.
"""

from __future__ import annotations

from app.domain.entities import Video
from app.domain.interfaces import IVideoRepository

# Stub — implementation in Phase 6


class VideoRepository(IVideoRepository):
    """PostgreSQL-backed repository for Video entity persistence."""

    def __init__(self, db_session) -> None:
        self.db = db_session

    async def save(self, video: Video) -> None:
        raise NotImplementedError("Phase 6: Implement PostgreSQL INSERT")

    async def get_by_id(self, video_id: str) -> Video | None:
        raise NotImplementedError("Phase 6: Implement PostgreSQL SELECT")

    async def update_status(self, video_id: str, status: str) -> None:
        raise NotImplementedError("Phase 6: Implement PostgreSQL UPDATE")
