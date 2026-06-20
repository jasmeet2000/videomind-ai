"""
Postgres video repository (async).

Optional dependency: asyncpg. Imports are lazy so unit tests and local runs
work without installing asyncpg. Use `connect()` before calling save/get.
"""
from __future__ import annotations

from typing import Any, Dict, Optional
import uuid
import datetime

from app.domain.entities import Video, VideoStatus
from app.domain.interfaces import IVideoRepository


class PostgresVideoRepository(IVideoRepository):
    """Async Postgres-backed video metadata repository using asyncpg."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self._pool = None

    async def connect(self) -> None:
        if self._pool is not None:
            return
        try:
            import asyncpg  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("asyncpg required for PostgresVideoRepository. Install with 'pip install asyncpg'") from exc

        self._pool = await asyncpg.create_pool(dsn=self.dsn, min_size=1, max_size=5)

    async def close(self) -> None:
        if self._pool is None:
            return
        await self._pool.close()
        self._pool = None

    async def save(self, video: Any) -> None:
        """Persist a video metadata record."""
        await self.connect()
        vid = video.id if hasattr(video, "id") else getattr(video, "id", str(uuid.uuid4()))
        filename = video.filename if hasattr(video, "filename") else ""
        file_path = video.file_path if hasattr(video, "file_path") else ""
        duration = video.duration_seconds if hasattr(video, "duration_seconds") else 0.0
        status = video.status.value if hasattr(video, "status") and hasattr(video.status, "value") else str(getattr(video, "status", "pending"))

        async with self._pool.acquire() as conn:
            # We assume a videos table with matching columns
            await conn.execute(
                """
                INSERT INTO videos (id, filename, file_path, duration_seconds, status)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (id) DO UPDATE SET
                    filename = EXCLUDED.filename,
                    file_path = EXCLUDED.file_path,
                    duration_seconds = EXCLUDED.duration_seconds,
                    status = EXCLUDED.status,
                    updated_at = NOW()
                """,
                vid,
                filename,
                file_path,
                duration,
                status,
            )

    async def get_by_id(self, video_id: str) -> Any | None:
        await self.connect()
        async with self._pool.acquire() as conn:
            r = await conn.fetchrow(
                "SELECT id, filename, file_path, duration_seconds, status, created_at, updated_at FROM videos WHERE id=$1",
                video_id,
            )
            if not r:
                return None
            
            # Map status string to Enum if possible
            try:
                status_enum = VideoStatus(r["status"])
            except ValueError:
                status_enum = VideoStatus.PENDING

            return Video(
                id=str(r["id"]),
                filename=r["filename"] if r["filename"] else "",
                file_path=r["file_path"] if r["file_path"] else "",
                duration_seconds=float(r["duration_seconds"]) if r["duration_seconds"] is not None else 0.0,
                status=status_enum,
                created_at=r["created_at"] if "created_at" in r else datetime.datetime.utcnow(),
                updated_at=r["updated_at"] if "updated_at" in r else datetime.datetime.utcnow(),
            )

    async def update_status(self, video_id: str, status: str) -> None:
        await self.connect()
        async with self._pool.acquire() as conn:
            await conn.execute("UPDATE videos SET status=$1, updated_at=NOW() WHERE id=$2", status, video_id)
