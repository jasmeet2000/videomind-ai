"""
VideoMind AI — Application Entry Point (Phase 2)
==================================================
Creates the FastAPI application with:
- Lifespan context manager (startup / shutdown hooks)
- Global exception handlers (domain exceptions → structured JSON)
- CORS middleware
- Health check routes
- Request-ID middleware for structured logging

Production requirements satisfied here:
- Structured logging with request_id on every request
- Custom exceptions → never expose stack traces to clients
- /health (liveness) and /health/ready (readiness) endpoints

SOLID — Single Responsibility:
    This file only wires the application together.
    No business logic, no ML calls, no DB queries live here.

Clean Architecture — Dependency Rule:
    Routes are registered here. Business logic lives in use cases.
    main.py imports from api/, core/ only.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import chat, health, search, video
from app.core.config import get_settings
from app.core.exceptions import VideoMindError
from app.core.logging import configure_logging, get_logger

logger = get_logger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Lifespan — startup and shutdown hooks
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    ASGI lifespan context manager.

    Startup: configure logging, validate critical settings.
    Shutdown: flush logs, close DB connections (added in Phase 6).

    Using lifespan (not on_event) is the FastAPI-recommended approach
    as of v0.93+. It keeps startup/shutdown logic in one place and
    makes the dependency lifecycle explicit.
    """
    # --- Startup ---
    configure_logging()
    logger.info(
        "VideoMind AI starting",
        version=settings.app_version,
        debug=settings.debug,
        log_level=settings.log_level,
    )

    # Provision optional external clients when readiness checks are enabled.
    # Lazy imports used so the app can run without the optional packages
    # during unit tests and local development.
    app.state.db_repo = None
    app.state.qdrant_repo = None
    app.state.video_repo = None

    if settings.check_readiness:
        try:
            from urllib.parse import urlparse
            parsed_db = urlparse(settings.database_url)
            db_scheme = (parsed_db.scheme or "").lower()

            if db_scheme.startswith("sqlite"):
                # Use SQLite-based repositories for local/CI
                from app.repositories.qdrant_vector_repository import QdrantVectorRepository
                from app.repositories.sqlite_transcript_repository import SQLiteTranscriptRepository
                from app.repositories.sqlite_video_repository import SQLiteVideoRepository

                db_path = parsed_db.path or ":memory:"
                # Normalize Windows absolute paths like /C:/path
                if db_path.startswith("/") and ":" in db_path:
                    db_path = db_path.lstrip("/")

                db_repo = SQLiteTranscriptRepository(db_path=db_path)
                video_repo = SQLiteVideoRepository(db_path=db_path)
                qdrant_repo = QdrantVectorRepository(
                    host=settings.qdrant_host,
                    port=settings.qdrant_port,
                    collection=settings.qdrant_collection_name,
                )

                # Connect asynchronously (implementations perform lazy imports)
                await db_repo.connect()
                await video_repo.connect()
                await qdrant_repo.connect()
            else:
                # Postgres + Qdrant (default)
                from app.repositories.postgres_transcript_repository import (
                    PostgresTranscriptRepository,
                )
                from app.repositories.postgres_video_repository import PostgresVideoRepository
                from app.repositories.qdrant_vector_repository import QdrantVectorRepository

                db_repo = PostgresTranscriptRepository(settings.database_url)
                qdrant_repo = QdrantVectorRepository(
                    host=settings.qdrant_host,
                    port=settings.qdrant_port,
                    collection=settings.qdrant_collection_name,
                )
                video_repo = PostgresVideoRepository(settings.database_url)

                # Connect asynchronously (implementations perform lazy imports)
                await db_repo.connect()
                await qdrant_repo.connect()
                await video_repo.connect()

            app.state.db_repo = db_repo
            app.state.qdrant_repo = qdrant_repo
            app.state.video_repo = video_repo

            logger.info("External clients initialized", db=("sqlite" if db_scheme.startswith("sqlite") else "postgres"), qdrant=settings.qdrant_host)
        except Exception as exc:
            logger.warning("Failed to initialize optional external clients", error=str(exc))

    yield

    # --- Shutdown ---
    # Close optional clients if they were initialized.
    try:
        if getattr(app.state, "qdrant_repo", None):
            await app.state.qdrant_repo.close()
    except Exception as exc:
        logger.warning("Error closing qdrant client", error=str(exc))

    try:
        if getattr(app.state, "db_repo", None):
            await app.state.db_repo.close()
    except Exception as exc:
        logger.warning("Error closing db client", error=str(exc))

    try:
        if getattr(app.state, "video_repo", None):
            await app.state.video_repo.close()
    except Exception as exc:
        logger.warning("Error closing video db client", error=str(exc))

    logger.info("VideoMind AI shutting down")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    """
    Application factory — creates and configures the FastAPI instance.

    DESIGN PATTERN — Factory:
        Using a factory instead of a module-level `app = FastAPI()` means
        tests can call create_app() to get a fresh, isolated instance with
        no shared state between test cases.

    Returns:
        Fully configured FastAPI application.
    """
    _app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Multi-modal video intelligence platform. "
            "Upload videos and query them via natural language."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # --- Middleware ---
    _register_middleware(_app)

    # --- Exception Handlers ---
    _register_exception_handlers(_app)

    # --- Routers ---
    _register_routers(_app)

    return _app


def _register_middleware(app: FastAPI) -> None:
    """
    Attach all middleware to the application.

    Middleware order matters — they execute in reverse registration order
    (last registered = first to run on request, last on response).
    """
    # CORS — allow Streamlit frontend on localhost
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8501"],  # Streamlit default
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request-ID middleware — injects a unique ID into every request.
    # Production requirement: every log line includes the request_id so
    # we can trace a full request across all log entries.
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        """Attach a unique request_id to each request for log correlation."""
        request_id = str(uuid.uuid4())
        # Store on request state so route handlers can access it
        request.state.request_id = request_id

        # Bind request_id to all log calls within this request's scope
        with logger.contextualize(request_id=request_id):
            logger.debug(
                "Request received",
                method=request.method,
                path=request.url.path,
            )
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            logger.debug(
                "Request completed",
                status_code=response.status_code,
            )
        return response


def _register_exception_handlers(app: FastAPI) -> None:
    """
    Register global exception handlers.

    Production requirement: custom exceptions → structured JSON.
    Stack traces NEVER reach the client.

    SOLID — Open/Closed:
        Adding a new exception class (e.g., RateLimitError) requires only
        adding one handler here. No route handler changes needed.
    """

    @app.exception_handler(VideoMindError)
    async def videomind_error_handler(
        request: Request, exc: VideoMindError
    ) -> JSONResponse:
        """Catch all domain exceptions and return a structured error response."""
        request_id = getattr(request.state, "request_id", "unknown")
        logger.warning(
            "Domain error",
            error_type=type(exc).__name__,
            message=exc.message,
            status_code=exc.status_code,
            request_id=request_id,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": type(exc).__name__,
                "message": exc.message,
                "request_id": request_id,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Catch-all for unexpected exceptions — never expose the traceback."""
        request_id = getattr(request.state, "request_id", "unknown")
        logger.exception(
            "Unhandled exception",
            request_id=request_id,
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "InternalServerError",
                "message": "An unexpected error occurred. Please try again.",
                "request_id": request_id,
            },
        )


def _register_routers(app: FastAPI) -> None:
    """
    Register all API routers.

    Routers are added here as each phase is completed.
    Phase 2: health only.
    Phase 9: video upload, search, chat.
    """
    # Phase 2: Health endpoints
    app.include_router(health.router, tags=["Health"])

    # Phase 9: Video, Search, Chat
    app.include_router(video.router, prefix="/api/v1/videos", tags=["Videos"])
    app.include_router(search.router, prefix="/api/v1", tags=["Search"])
    app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])


# ---------------------------------------------------------------------------
# Application instance (module-level — used by uvicorn)
# ---------------------------------------------------------------------------
app = create_app()
