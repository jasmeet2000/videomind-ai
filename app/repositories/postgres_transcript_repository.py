"""
Postgres transcript repository (async).

Optional dependency: asyncpg. Imports are lazy so unit tests and local runs
work without installing asyncpg. Use `connect()` before calling save/get.
"""

from __future__ import annotations

import contextlib
import json

from app.domain.entities import TranscriptChunk
from app.domain.interfaces import ITranscriptRepository


class PostgresTranscriptRepository(ITranscriptRepository):
    """Async Postgres-backed transcript repository using asyncpg."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self._pool = None

    async def connect(self) -> None:
        """Lazily create an asyncpg pool. Raises RuntimeError if asyncpg
        is not installed with an actionable message.
        """
        if self._pool is not None:
            return
        try:
            import asyncpg  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "asyncpg required for PostgresTranscriptRepository. Install with 'pip install asyncpg'"
            ) from exc

        self._pool = await asyncpg.create_pool(dsn=self.dsn, min_size=1, max_size=5)

    async def close(self) -> None:
        if self._pool is None:
            return
        await self._pool.close()
        self._pool = None

    async def save_batch(self, chunks: list[TranscriptChunk]) -> None:
        """Persist a batch of TranscriptChunk objects.

        Uses executemany for efficiency.
        """
        await self.connect()

        rows = []
        for c in chunks:
            rows.append(
                (
                    str(c.video_id),
                    c.text,
                    float(c.start_seconds),
                    float(c.end_seconds) if c.end_seconds is not None else 0.0,
                    json.dumps(c.embedding) if getattr(c, "embedding", None) is not None else None,
                )
            )

        async with self._pool.acquire() as conn:
            async with conn.transaction():
                await conn.executemany(
                    "INSERT INTO transcript_chunks (video_id, text, start_seconds, end_seconds, embedding) VALUES ($1,$2,$3,$4,$5)",
                    rows,
                )

    async def get_by_video_id(self, video_id: str) -> list[TranscriptChunk]:
        await self.connect()
        async with self._pool.acquire() as conn:
            records = await conn.fetch(
                "SELECT id, video_id, text, start_seconds, end_seconds, embedding FROM transcript_chunks WHERE video_id=$1 ORDER BY start_seconds",
                video_id,
            )
            result: list[TranscriptChunk] = []
            for r in records:
                embedding = r["embedding"]
                if embedding is not None and isinstance(embedding, (str, bytes)):
                    with contextlib.suppress(Exception):
                        embedding = json.loads(embedding)

                tc = TranscriptChunk(
                    id=str(r["id"]),
                    video_id=str(r["video_id"]),
                    text=r["text"],
                    start_seconds=float(r["start_seconds"]),
                    end_seconds=float(r["end_seconds"]),
                )
                if embedding is not None:
                    tc.embedding = embedding
                result.append(tc)
            return result
