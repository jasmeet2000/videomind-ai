"""
Qdrant vector repository adapter.

Supports qdrant-client Python library if installed, otherwise falls
back to the HTTP API via requests. Blocking calls are executed in a
thread to avoid blocking the event loop.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from app.domain.entities import SearchResult


class QdrantVectorRepository:
    """Adapter for Qdrant. Optional dependency on qdrant-client.

    The implementation is intentionally permissive: it tries to use the
    qdrant-client package first, and if unavailable uses the REST API
    via requests. All network/blocking calls run in a thread.
    """

    def __init__(self, host: str = "localhost", port: int = 6333, collection: str = "videomind") -> None:
        self.host = host
        self.port = int(port)
        self.collection = collection
        self._client = None
        self._use_http = False
        self._base_url: str | None = None

    async def connect(self) -> None:
        if self._client is not None:
            return
        try:
            from qdrant_client import QdrantClient  # type: ignore

            # qdrant-client may perform startup work; instantiate lazily
            self._client = QdrantClient(host=self.host, port=self.port)
            self._use_http = False
        except Exception:
            # Fallback to requests-based HTTP client
            import requests  # type: ignore

            self._client = requests.Session()
            self._base_url = f"http://{self.host}:{self.port}"
            self._use_http = True

    async def close(self) -> None:
        if self._client is None:
            return
        if self._use_http:
            try:
                self._client.close()
            except Exception:
                pass
        # qdrant-client has no explicit close API
        self._client = None

    async def upsert(self, points: List[Dict[str, Any]], collection: str | None = None) -> None:
        collection = collection or self.collection
        await self.connect()
        if not self._use_http:
            # Blocking call — run in a thread
            await asyncio.to_thread(self._client.upsert, collection_name=collection, points=points)
        else:
            url = f"{self._base_url}/collections/{collection}/points?wait=true"
            await asyncio.to_thread(self._client.put, url, json={"points": points}, timeout=15)

    async def search(self, vector: List[float], collection: str | None = None, video_id: str | None = None, top_k: int = 10) -> List[SearchResult]:
        collection = collection or self.collection
        await self.connect()
        results: List[SearchResult] = []
        if not self._use_http:
            resp = await asyncio.to_thread(self._client.search, collection_name=collection, query_vector=vector, limit=top_k, with_payload=True)
            for hit in resp:
                payload = getattr(hit, "payload", {}) or {}
                results.append(
                    SearchResult(
                        chunk_id=str(hit.id),
                        video_id=payload.get("video_id"),
                        modality=payload.get("modality"),
                        text=payload.get("text"),
                        score=getattr(hit, "score", 0.0),
                        start_seconds=payload.get("start_seconds", 0.0),
                        end_seconds=payload.get("end_seconds"),
                        metadata=payload,
                    )
                )
            return results
        else:
            url = f"{self._base_url}/collections/{collection}/points/search"
            payload = {"vector": vector, "top": top_k}
            resp = await asyncio.to_thread(self._client.post, url, json=payload, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("result", []):
                payload = item.get("payload", {}) or {}
                results.append(
                    SearchResult(
                        chunk_id=str(item.get("id")),
                        video_id=payload.get("video_id"),
                        modality=payload.get("modality"),
                        text=payload.get("text"),
                        score=item.get("score", 0.0),
                        start_seconds=payload.get("start_seconds", 0.0),
                        end_seconds=payload.get("end_seconds"),
                        metadata=payload,
                    )
                )
            return results
