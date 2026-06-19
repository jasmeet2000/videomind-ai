"""
SQLite-backed transcript repository implementing ITranscriptRepository.

This implementation uses the standard library sqlite3 in a thread via
asyncio.to_thread so it remains compatible with the asynchronous
application code without requiring async DB drivers.
"""
from __future__ import annotations

import json
import sqlite3
import os
import asyncio
import uuid
from typing import List, Optional

from app.domain.interfaces import ITranscriptRepository
from app.domain.entities import TranscriptChunk


class SQLiteTranscriptRepository(ITranscriptRepository):
    """SQLite-backed implementation of ITranscriptRepository."""

    def __init__(self, db_path: str = "data\videomind.db") -> None:
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    async def connect(self) -> None:
        if self._conn is not None:
            return
        # Ensure parent directory exists (unless using :memory:)
        if self.db_path != ":memory:":
            parent = os.path.dirname(self.db_path)
            if parent:
                os.makedirs(parent, exist_ok=True)

        def _open():
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.execute("PRAGMA foreign_keys = ON;")
            return conn

        self._conn = await asyncio.to_thread(_open)
        await asyncio.to_thread(self._ensure_tables)

    def _ensure_tables(self) -> None:
        cur = self._conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS transcript_chunks (
                id TEXT PRIMARY KEY,
                video_id TEXT NOT NULL,
                content TEXT NOT NULL,
                start_time REAL NOT NULL,
                end_time REAL NOT NULL,
                embedding TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_transcript_video_id ON transcript_chunks(video_id);")
        self._conn.commit()

    async def close(self) -> None:
        if self._conn is None:
            return
        await asyncio.to_thread(self._conn.close)
        self._conn = None

    async def save_batch(self, chunks: list[TranscriptChunk]) -> None:
        """Persist a batch of TranscriptChunk objects."""
        await self.connect()

        def _save() -> None:
            cur = self._conn.cursor()
            rows = []
            for c in chunks:
                cid = getattr(c, "id", None) or str(uuid.uuid4())
                # domain entity uses 'text' for content
                text = getattr(c, "text", getattr(c, "content", ""))
                embedding = getattr(c, "embedding", None)
                embedding_json = json.dumps(embedding) if embedding is not None else None
                rows.append((cid, str(c.video_id), text, float(c.start_seconds), float(c.end_seconds) if getattr(c, "end_seconds", None) is not None else 0.0, embedding_json))

            cur.executemany(
                """
                INSERT OR REPLACE INTO transcript_chunks (id, video_id, content, start_time, end_time, embedding)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
            self._conn.commit()

        await asyncio.to_thread(_save)

    async def get_by_video_id(self, video_id: str) -> list[TranscriptChunk]:
        await self.connect()

        def _get() -> list[TranscriptChunk]:
            cur = self._conn.cursor()
            cur.execute(
                "SELECT id, video_id, content, start_time, end_time, embedding FROM transcript_chunks WHERE video_id=? ORDER BY start_time",
                (video_id,),
            )
            rows = cur.fetchall()
            result: list[TranscriptChunk] = []
            for r in rows:
                embedding_raw = r[5]
                embedding = None
                if embedding_raw:
                    try:
                        embedding = json.loads(embedding_raw)
                    except Exception:
                        embedding = None

                tc = TranscriptChunk(
                    id=str(r[0]),
                    video_id=str(r[1]),
                    text=r[2],
                    start_seconds=float(r[3]),
                    end_seconds=float(r[4]),
                )
                # attach embedding attribute if the dataclass doesn't define it
                try:
                    setattr(tc, "embedding", embedding)
                except Exception:
                    pass
                result.append(tc)
            return result

        return await asyncio.to_thread(_get)
