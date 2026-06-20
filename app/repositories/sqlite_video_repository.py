"""
SQLite-backed video metadata repository implementing IVideoRepository.

Uses sqlite3 via asyncio.to_thread for compatibility with the async app.
"""
from __future__ import annotations

import asyncio
import os
import sqlite3
import datetime
from typing import Any, Dict, Optional
import uuid

from app.domain.entities import Video, VideoStatus
from app.domain.interfaces import IVideoRepository


class SQLiteVideoRepository(IVideoRepository):
    """SQLite-backed implementation of IVideoRepository."""

    def __init__(self, db_path: str = "data\videomind.db") -> None:
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    async def connect(self) -> None:
        if self._conn is not None:
            return
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
            CREATE TABLE IF NOT EXISTS videos (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                duration_seconds REAL,
                status TEXT DEFAULT 'uploaded',
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_videos_created_at ON videos(created_at);")
        self._conn.commit()

    async def close(self) -> None:
        if self._conn is None:
            return
        await asyncio.to_thread(self._conn.close)
        self._conn = None

    async def save(self, video: Any) -> None:
        await self.connect()

        def _save() -> None:
            cur = self._conn.cursor()
            vid = video.id if hasattr(video, "id") else getattr(video, "id", str(uuid.uuid4()))
            filename = video.filename if hasattr(video, "filename") else ""
            file_path = video.file_path if hasattr(video, "file_path") else ""
            duration = video.duration_seconds if hasattr(video, "duration_seconds") else 0.0
            status = video.status.value if hasattr(video, "status") and hasattr(video.status, "value") else str(getattr(video, "status", "pending"))

            # Insert or replace; preserve existing status if present
            cur.execute(
                """
                INSERT OR REPLACE INTO videos (id, filename, file_path, duration_seconds, status, updated_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
                """,
                (vid, filename, file_path, duration, status),
            )
            self._conn.commit()

        await asyncio.to_thread(_save)

    async def get_by_id(self, video_id: str) -> Any | None:
        await self.connect()

        def _get() -> Any | None:
            cur = self._conn.cursor()
            cur.execute(
                "SELECT id, filename, file_path, duration_seconds, status, created_at, updated_at FROM videos WHERE id = ?",
                (video_id,),
            )
            r = cur.fetchone()
            if not r:
                return None
            
            try:
                status_enum = VideoStatus(r[4])
            except ValueError:
                status_enum = VideoStatus.PENDING

            created_at = datetime.datetime.fromisoformat(r[5]) if r[5] else datetime.datetime.utcnow()
            updated_at = datetime.datetime.fromisoformat(r[6]) if r[6] else datetime.datetime.utcnow()

            return Video(
                id=r[0],
                filename=r[1] if r[1] else "",
                file_path=r[2] if r[2] else "",
                duration_seconds=float(r[3]) if r[3] is not None else 0.0,
                status=status_enum,
                created_at=created_at,
                updated_at=updated_at,
            )

        return await asyncio.to_thread(_get)

    async def update_status(self, video_id: str, status: str) -> None:
        await self.connect()

        def _update() -> None:
            cur = self._conn.cursor()
            cur.execute("UPDATE videos SET status=?, updated_at=datetime('now') WHERE id=?", (status, video_id))
            self._conn.commit()

        await asyncio.to_thread(_update)
