"""
VideoMind AI — FastAPI Dependency Injection (Phase 2)
======================================================
Provides dependency functions for FastAPI's DI system.
Each function returns a service or repository instance, injected into
route handlers via `Depends()`.

SOLID — Dependency Inversion:
    Route handlers depend on interfaces returned by these functions.
    The concrete implementation (real vs. mock) is swapped at the DI layer.

DESIGN PATTERN — Singleton via module-level caching:
    Expensive resources (DB pool, Qdrant client, model registry) are
    instantiated once at startup and reused. FastAPI's DI system calls
    these functions on every request, but the expensive object is cached
    at module level.

Phase 2: All functions return None stubs.
Phase 6: Real clients injected after Docker services are available.
"""

from __future__ import annotations

from app.core.config import get_settings

settings = get_settings()

# ---------------------------------------------------------------------------
# Phase 6+: DB session pool (asyncpg / SQLAlchemy async)
# ---------------------------------------------------------------------------
# _db_pool: asyncpg.Pool | None = None
#
# async def get_db():
#     """Yield an async DB connection from the pool."""
#     async with _db_pool.acquire() as conn:
#         yield conn

async def get_db():
    """
    Stub: yields a DB session.
    Phase 6: Replace with real asyncpg pool connection.
    """
    # TODO (Phase 6): Replace with real pool.acquire()
    yield None


# ---------------------------------------------------------------------------
# Phase 6+: Qdrant client (Singleton)
# ---------------------------------------------------------------------------
# _qdrant_client: QdrantClient | None = None
#
# def get_qdrant_client() -> QdrantClient:
#     global _qdrant_client
#     if _qdrant_client is None:
#         _qdrant_client = QdrantClient(
#             host=settings.qdrant_host,
#             port=settings.qdrant_port,
#         )
#     return _qdrant_client

_qdrant_client = None

def get_qdrant_client():
    """
    Return a singleton Qdrant vector repository adapter.

    This returns an instance of QdrantVectorRepository which encapsulates
    the Python client or HTTP fallback and exposes async `upsert` and
    `search` methods used by the VectorRepository.
    """
    global _qdrant_client
    if _qdrant_client is not None:
        return _qdrant_client

    # Lazy-import to avoid importing heavy optional deps at module import time
    from app.repositories.qdrant_vector_repository import QdrantVectorRepository

    _qdrant_client = QdrantVectorRepository(host=settings.qdrant_host, port=settings.qdrant_port, collection=settings.qdrant_collection_name)
    return _qdrant_client


# ---------------------------------------------------------------------------
# Phase 6+: Use case providers
# ---------------------------------------------------------------------------

def get_ingest_use_case():
    """
    Provide an IngestVideoUseCase with all dependencies wired in.
    Phase 6: Wire VideoRepository, TranscriptRepository, VectorRepository,
             EmbeddingService, WhisperService, OCRService.
    """
    return None


def get_search_use_case():
    """
    Provide a SearchVideoUseCase with retrieval pipeline wired in.
    Phase 7: Wire HybridRetriever, CrossEncoderReranker, EmbeddingService.
    """
    return None


def get_chat_use_case():
    """
    Provide a ChatWithVideoUseCase with full RAG pipeline wired in.
    Phase 8: Wire EmbeddingService, HybridRetriever, LLMService,
             PromptBuilder, ContextBuilder.
    """
    return None
