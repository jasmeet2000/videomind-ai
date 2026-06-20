"""
Qdrant vector repository adapter.

Supports qdrant-client Python library if installed, otherwise falls
back to the HTTP API via requests. Blocking calls are executed in a
thread to avoid blocking the event loop.
"""

from __future__ import annotations

import asyncio
import contextlib
from typing import Any

from app.domain.entities import SearchResult


class QdrantVectorRepository:
    """Adapter for Qdrant. Optional dependency on qdrant-client.

    The implementation is intentionally permissive: it tries to use the
    qdrant-client package first, and if unavailable uses the REST API
    via requests. All network/blocking calls run in a thread.
    """

    def __init__(
        self, host: str = "localhost", port: int = 6333, collection: str = "videomind"
    ) -> None:
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
            with contextlib.suppress(Exception):
                self._client.close()
        # qdrant-client has no explicit close API
        self._client = None

    async def upsert(self, points: list[dict[str, Any]], collection: str | None = None) -> None:
        collection = collection or self.collection
        await self.connect()
        if not self._use_http:
            # Convert simple dicts into qdrant-client PointStruct objects when available
            qdrant_points = points
            try:
                try:
                    from qdrant_client.http import models as qdrant_models  # type: ignore
                except Exception:
                    from qdrant_client import models as qdrant_models  # type: ignore

                qdrant_points = []
                for p in points:
                    pid = p.get("id")
                    vec = p.get("vector")
                    payload = p.get("payload", {}) or {}
                    qdrant_points.append(
                        qdrant_models.PointStruct(id=pid, vector=vec, payload=payload)
                    )
            except Exception:
                # If constructing PointStructs fails, fall back to raw dicts
                qdrant_points = points

            # Blocking call — run in a thread
            await asyncio.to_thread(
                self._client.upsert, collection_name=collection, points=qdrant_points
            )
        else:
            url = f"{self._base_url}/collections/{collection}/points?wait=true"
            await asyncio.to_thread(self._client.put, url, json={"points": points}, timeout=15)

    async def search(
        self,
        vector: list[float],
        collection: str | None = None,
        video_id: str | None = None,
        top_k: int = 10,
    ) -> list[SearchResult]:
        collection = collection or self.collection
        await self.connect()
        results: list[SearchResult] = []
        if not self._use_http:
            # Build search kwargs and optionally attach a Filter when video_id is provided
            kwargs: dict = {
                "collection_name": collection,
                "query": vector,
                "limit": top_k,
                "with_payload": True,
            }
            if video_id is not None:
                filter_obj = None
                try:
                    # qdrant-client v1+ exposes models under http.models
                    try:
                        from qdrant_client.http import models as qdrant_models  # type: ignore
                    except Exception:
                        from qdrant_client import models as qdrant_models  # type: ignore

                    filter_obj = qdrant_models.Filter(
                        must=[
                            qdrant_models.FieldCondition(
                                key="video_id",
                                match=qdrant_models.MatchValue(value=video_id),
                            )
                        ]
                    )
                except Exception:
                    filter_obj = None

                if filter_obj is not None:
                    kwargs["query_filter"] = filter_obj

            try:
                resp = await asyncio.to_thread(self._client.query_points, **kwargs)
            except Exception as e:
                # Catch qdrant_client.http.exceptions.UnexpectedResponse for "doesn't exist"
                if "doesn't exist" in str(e) or "Not found" in str(e):
                    return []
                raise

            for hit in resp.points:
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
            if video_id is not None:
                payload["filter"] = {"must": [{"key": "video_id", "match": {"value": video_id}}]}
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
