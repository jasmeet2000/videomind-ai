"""
Postgres video repository (async).

Optional dependency: asyncpg. Imports are lazy so unit tests and local runs
work without installing asyncpg. Use `connect()` before calling save/get.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

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

    async def save(self, video: Dict[str, Any]) -> None:
        """Persist a video metadata record. Accepts optional 'id'."""
        await self.connect()
        vid = video.get("id")
        source_uri = video.get("source_uri")
        duration = video.get("duration_seconds")

        async with self._pool.acquire() as conn:
            if vid:
                await conn.execute(
                    "INSERT INTO videos (id, source_uri, duration_seconds) VALUES ($1,$2,$3) "
                    "ON CONFLICT (id) DO UPDATE SET source_uri = EXCLUDED.source_uri, duration_seconds = EXCLUDED.duration_seconds",
                    vid,
                    source_uri,
                    duration,
                )
            else:
                await conn.execute(
                    "INSERT INTO videos (source_uri, duration_seconds) VALUES ($1,$2)",
                    source_uri,
                    duration,
                )

    async def get_by_id(self, video_id: str) -> Optional[Dict[str, Any]]:
        await self.connect()
        async with self._pool.acquire() as conn:
            r = await conn.fetchrow(
                "SELECT id, source_uri, duration_seconds, created_at FROM videos WHERE id=$1",
                video_id,
            )
            if not r:
                return None
            return {
                "id": str(r["id"]),
                "source_uri": r["source_uri"],
                "duration_seconds": float(r["duration_seconds"]) if r["duration_seconds"] is not None else None,
                "created_at": r["created_at"],
            }

    async def update_status(self, video_id: str, status: str) -> None:
        await self.connect()
        async with self._pool.acquire() as conn:
            await conn.execute("UPDATE videos SET status=$1 WHERE id=$2", status, video_id)
