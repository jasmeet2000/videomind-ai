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

PERFORMANCE — Singleton Caching:
    All ML model instances (BGE embeddings, CrossEncoder reranker) and
    use-case objects are cached as module-level singletons. This avoids
    re-loading multi-hundred-MB models on every API request.

Phase 2: All functions return None stubs.
Phase 6: Real clients injected after Docker services are available.
"""

from __future__ import annotations

from app.core.config import get_settings

settings = get_settings()

# ---------------------------------------------------------------------------
# Singleton caches — heavy objects loaded once and reused across requests.
# This is the #1 performance optimization: without caching, each /search
# or /chat request would re-load the BGE model (~200ms), CrossEncoder
# (~500ms), and reconstruct the entire retrieval pipeline from scratch.
# ---------------------------------------------------------------------------
_ingest_use_case = None
_search_use_case = None
_chat_use_case = None

# Shared ML model singletons — used by both search and chat pipelines.
# The BGE embedding model and CrossEncoder reranker are stateless at
# inference time, so sharing a single instance is safe.
_shared_bge_model = None
_shared_reranker = None
_shared_embedding_service = None


def _get_shared_bge_model():
    """Return a singleton BGEEmbeddingModel, loading it once."""
    global _shared_bge_model
    if _shared_bge_model is None:
        from app.embeddings.bge_model import BGEEmbeddingModel
        _shared_bge_model = BGEEmbeddingModel(model_name=settings.embedding_model)
    return _shared_bge_model


def _get_shared_embedding_service():
    """Return a singleton EmbeddingService wrapping the shared BGE model."""
    global _shared_embedding_service
    if _shared_embedding_service is None:
        from app.embeddings.service import EmbeddingService
        _shared_embedding_service = EmbeddingService(model=_get_shared_bge_model())
    return _shared_embedding_service


def _get_shared_reranker():
    """Return a singleton CrossEncoderReranker, loading it once."""
    global _shared_reranker
    if _shared_reranker is None:
        from app.retrieval.reranker import CrossEncoderReranker
        _shared_reranker = CrossEncoderReranker()
    return _shared_reranker


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
    Yield an asyncpg connection from a lazily-created pool.

    Falls back to yielding None when asyncpg isn't installed or when no
    database URL is configured (useful for local development and tests).
    """
    global _db_pool
    # Ensure module-level variable exists
    if "_db_pool" not in globals():
        _db_pool = None

    dsn = getattr(settings, "database_url", None)
    if not dsn:
        # No database configured — yield None so callers can operate in-memory
        yield None
        return

    if _db_pool is None:
        try:
            import asyncpg  # type: ignore
        except Exception:
            # Optional dependency not installed — fall back to None
            yield None
            return
        # Create a small pool for application usage
        _db_pool = await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=5)

    async with _db_pool.acquire() as conn:
        yield conn


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

    _qdrant_client = QdrantVectorRepository(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        collection=settings.qdrant_collection_name,
    )
    return _qdrant_client


# ---------------------------------------------------------------------------
# Phase 6+: Use case providers (singleton-cached)
# ---------------------------------------------------------------------------


def get_ingest_use_case():
    """
    Provide an IngestVideoUseCase with all dependencies wired in.

    PERFORMANCE: Cached as a singleton. The internal WhisperService and
    VideoProcessor are stateful (lazy-loaded models) and benefit from
    being reused across multiple video uploads.

    This function performs conservative, lazy wiring so the application can
    run without optional heavy dependencies in development. Preference order:
      - SQLite (when DATABASE_URL points to sqlite)
      - Postgres (when DATABASE_URL points to postgres)
      - In-memory fallback
    """
    global _ingest_use_case
    if _ingest_use_case is not None:
        return _ingest_use_case

    # Lazy imports to avoid pulling optional deps at module import time
    from app.use_cases.ingest_video import IngestVideoUseCase

    video_repo = None
    transcript_repo = None

    dsn = getattr(settings, "database_url", "") or ""

    try:
        if dsn.startswith("sqlite"):
            from app.repositories.sqlite_transcript_repository import SQLiteTranscriptRepository
            from app.repositories.sqlite_video_repository import SQLiteVideoRepository

            db_path = "data\\videomind.db"
            video_repo = SQLiteVideoRepository(db_path=db_path)
            transcript_repo = SQLiteTranscriptRepository(db_path=db_path)
        elif dsn:
            # Assume a Postgres-style DSN
            from app.repositories.postgres_transcript_repository import PostgresTranscriptRepository
            from app.repositories.postgres_video_repository import PostgresVideoRepository

            video_repo = PostgresVideoRepository(dsn=dsn)
            transcript_repo = PostgresTranscriptRepository(dsn=dsn)
    except Exception:
        # If any optional dependency is missing or initialization fails,
        # fall back to in-memory implementations so the app remains usable.
        from app.repositories.in_memory_transcript_repository import InMemoryTranscriptRepository
        from app.repositories.in_memory_video_repository import InMemoryVideoRepository

        transcript_repo = transcript_repo or InMemoryTranscriptRepository()
        video_repo = video_repo or InMemoryVideoRepository()

    # Wire the light-weight runtime services used by the Ingest use case
    from app.speech.whisper_service import WhisperService
    from app.video.processor import VideoProcessor

    _ingest_use_case = IngestVideoUseCase(
        video_processor=VideoProcessor(),
        whisper_service=WhisperService(),
        transcript_repo=transcript_repo,
        video_repo=video_repo,
    )
    return _ingest_use_case


def get_search_use_case():
    """
    Provide a SearchVideoUseCase with retrieval pipeline wired in.

    PERFORMANCE: Cached as a singleton. Shares the BGE embedding model
    and CrossEncoder reranker with the chat pipeline to avoid loading
    these ~500MB+ models multiple times.
    """
    global _search_use_case
    if _search_use_case is not None:
        return _search_use_case

    from app.repositories.in_memory_transcript_repository import InMemoryTranscriptRepository
    from app.retrieval.dense import DenseRetriever
    from app.retrieval.hybrid import HybridRetriever
    from app.retrieval.sparse import BM25SparseRetriever
    from app.use_cases.search_video import SearchVideoUseCase

    # For Phase 9 local testing without full docker DBs, we'll instantiate with in-memory fallbacks
    # if qdrant/db are not reachable, but ideally use the wired clients.
    qdrant = get_qdrant_client()

    dense = DenseRetriever(vector_repo=qdrant, collection=settings.qdrant_collection_name)
    sparse = BM25SparseRetriever(
        transcript_repo=InMemoryTranscriptRepository()
    )  # Ideally inject real DB

    hybrid = HybridRetriever(dense_retriever=dense, sparse_retriever=sparse)

    _search_use_case = SearchVideoUseCase(
        embedding_model=_get_shared_embedding_service(),
        retriever=hybrid,
        reranker=_get_shared_reranker(),
    )
    return _search_use_case


def get_chat_use_case():
    """
    Provide a ChatWithVideoUseCase with full RAG pipeline wired in.

    PERFORMANCE: Cached as a singleton. Shares the BGE embedding model
    and CrossEncoder reranker with the search pipeline.
    """
    global _chat_use_case
    if _chat_use_case is not None:
        return _chat_use_case

    from app.generation.context_builder import ContextBuilder
    from app.generation.llm_service import OllamaClient
    from app.generation.prompt_builder import PromptBuilder
    from app.repositories.in_memory_transcript_repository import InMemoryTranscriptRepository
    from app.retrieval.dense import DenseRetriever
    from app.retrieval.hybrid import HybridRetriever
    from app.retrieval.sparse import BM25SparseRetriever
    from app.use_cases.chat_with_video import ChatWithVideoUseCase

    qdrant = get_qdrant_client()

    dense = DenseRetriever(vector_repo=qdrant, collection=settings.qdrant_collection_name)
    sparse = BM25SparseRetriever(transcript_repo=InMemoryTranscriptRepository())

    hybrid = HybridRetriever(dense_retriever=dense, sparse_retriever=sparse)

    llm = OllamaClient(host=settings.ollama_host, model=settings.ollama_model)

    _chat_use_case = ChatWithVideoUseCase(
        embedding_model=_get_shared_bge_model(),
        retriever=hybrid,
        reranker=_get_shared_reranker(),
        llm_backend=llm,
        context_builder=ContextBuilder(),
        prompt_builder=PromptBuilder(),
    )
    return _chat_use_case
