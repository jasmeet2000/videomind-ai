"""
SQLite-backed video metadata repository implementing IVideoRepository.

Uses sqlite3 via asyncio.to_thread for compatibility with the async app.
"""
from __future__ import annotations

import sqlite3
import os
import asyncio
import uuid
from typing import Any, Dict, Optional

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
                source_uri TEXT NOT NULL,
                duration_seconds REAL,
                status TEXT DEFAULT 'uploaded',
                created_at TEXT DEFAULT (datetime('now'))
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

    async def save(self, video: Dict[str, Any]) -> None:
        await self.connect()

        def _save() -> None:
            cur = self._conn.cursor()
            vid = video.get("id") or str(uuid.uuid4())
            source_uri = video.get("source_uri")
            duration = video.get("duration_seconds")

            # Insert or replace; preserve existing status if present
            cur.execute(
                """
                INSERT OR REPLACE INTO videos (id, source_uri, duration_seconds, status)
                VALUES (?, ?, ?, COALESCE((SELECT status FROM videos WHERE id = ?), 'uploaded'))
                """,
                (vid, source_uri, duration, vid),
            )
            self._conn.commit()

        await asyncio.to_thread(_save)

    async def get_by_id(self, video_id: str) -> Optional[Dict[str, Any]]:
        await self.connect()

        def _get() -> Optional[Dict[str, Any]]:
            cur = self._conn.cursor()
            cur.execute(
                "SELECT id, source_uri, duration_seconds, status, created_at FROM videos WHERE id = ?",
                (video_id,),
            )
            r = cur.fetchone()
            if not r:
                return None
            return {
                "id": r[0],
                "source_uri": r[1],
                "duration_seconds": float(r[2]) if r[2] is not None else None,
                "status": r[3],
                "created_at": r[4],
            }

        return await asyncio.to_thread(_get)

    async def update_status(self, video_id: str, status: str) -> None:
        await self.connect()

        def _update() -> None:
            cur = self._conn.cursor()
            cur.execute("UPDATE videos SET status=? WHERE id=?", (status, video_id))
            self._conn.commit()

        await asyncio.to_thread(_update)
