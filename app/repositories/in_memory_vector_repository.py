from __future__ import annotations

import math
from typing import Any

from app.domain.entities import SearchResult
from app.domain.interfaces import IVectorRepository


class InMemoryVectorRepository(IVectorRepository):
    """A simple in-memory vector store for testing and CI."""

    def __init__(self) -> None:
        # collection -> list of {'id': str, 'vector': list[float], 'payload': dict}
        self.store: dict[str, list[dict[str, Any]]] = {}

    async def upsert(self, chunks: list[dict[str, Any]], collection: str) -> None:
        bucket = self.store.setdefault(collection, [])
        for c in chunks:
            # naive append; overwrite if id exists
            existing = next((x for x in bucket if x["id"] == c["id"]), None)
            if existing:
                existing.update(c)
            else:
                bucket.append(c.copy())

    async def search(self, query_vector: list[float], collection: str, video_id: str, top_k: int):
        candidates = []
        for item in self.store.get(collection, []):
            payload = item.get("payload", {})
            if payload.get("video_id") != video_id:
                continue
            vec = item.get("vector", [])
            # cosine similarity
            dot = sum(a * b for a, b in zip(query_vector, vec))
            norm_q = math.sqrt(sum(a * a for a in query_vector))
            norm_v = math.sqrt(sum(a * a for a in vec))
            score = (dot / (norm_q * norm_v)) if norm_q > 0 and norm_v > 0 else 0.0
            candidates.append((score, item))

        candidates.sort(key=lambda t: t[0], reverse=True)
        results: list[SearchResult] = []
        for score, item in candidates[:top_k]:
            payload = item.get("payload", {})
            results.append(
                SearchResult(
                    chunk_id=item.get("id", ""),
                    video_id=payload.get("video_id", ""),
                    modality=payload.get("modality", None),
                    text=payload.get("text", ""),
                    score=score,
                    start_seconds=payload.get("start_seconds", 0.0),
                    end_seconds=payload.get("end_seconds", None),
                    metadata=payload,
                )
            )
        return results
