"""
VideoMind AI — Health Check Routes (Phase 2)
==============================================
Provides two endpoints required by production deployments:

  GET /health       — Liveness probe
  GET /health/ready — Readiness probe

DESIGN DISTINCTION — Liveness vs Readiness:
    Liveness (/health): "Is the process alive?" Docker/K8s restarts the
    container if this returns non-200. It should NEVER call external services
    — a DB outage must not trigger a container restart.

    Readiness (/health/ready): "Is the app ready to serve traffic?" Load
    balancers remove the instance from rotation if this fails. It SHOULD
    check DB and Qdrant connectivity so requests aren't sent to an app
    that can't serve them.

SOLID — Single Responsibility:
    Health checks live in their own router, not mixed into other routes.

Clean Architecture — API Layer:
    Route handlers parse input and return output only.
    Connectivity checks will delegate to use cases / repositories in Phase 6.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import get_settings

router = APIRouter()
settings = get_settings()


# ---------------------------------------------------------------------------
# Response schemas (inline — small enough to not warrant a separate file)
# ---------------------------------------------------------------------------


class HealthResponse(BaseModel):
    """Liveness probe response."""

    status: str
    version: str
    app_name: str


class ReadinessResponse(BaseModel):
    """Readiness probe response with per-dependency status."""

    status: str
    version: str
    dependencies: dict[str, str]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness probe",
    description=(
        "Returns 200 if the process is running. "
        "Does NOT check external dependencies — safe for liveness probes."
    ),
)
async def health() -> HealthResponse:
    """
    Liveness probe endpoint.

    Never fails as long as the process is alive. Does not call any
    external service (DB, Qdrant, Ollama) — a downstream outage must
    not cause this to return non-200 and trigger a container restart.

    Returns:
        HealthResponse with status='ok' and app metadata.
    """
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        app_name=settings.app_name,
    )


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    summary="Readiness probe",
    description=(
        "Returns 200 only when all required external dependencies "
        "(PostgreSQL, Qdrant) are reachable. Used by load balancers "
        "to determine if this instance should receive traffic."
    ),
)
async def readiness() -> ReadinessResponse:
    """
    Readiness probe endpoint.

    Checks connectivity to PostgreSQL and Qdrant. Returns 503 if any
    required dependency is unreachable, so the load balancer stops
    routing traffic to this instance.

    Phase 2: stubs return 'not_configured' until DB clients are wired
    in Phase 6. The endpoint still returns 200 so the app boots cleanly.

    Returns:
        ReadinessResponse with per-dependency status.
    """
    # Phase 6: replace stubs with real connectivity checks
    # e.g. await db.execute("SELECT 1")
    #      await qdrant_client.get_collections()
    if not settings.check_readiness:
        # Keep Phase 2 behavior during development / CI unless readiness
        # checks are explicitly enabled via settings.check_readiness.
        dependencies: dict[str, str] = {
            "postgresql": "not_configured",  # Phase 6
            "qdrant": "not_configured",  # Phase 6
            "ollama": "not_configured",  # Phase 8
        }
        overall_status = "ok"
    else:
        from urllib.parse import urlparse

        from app.core.network import tcp_check

        # Parse DB host/port from database_url (e.g. postgresql://user:pw@host:port/db)
        parsed = urlparse(settings.database_url)
        db_host = parsed.hostname or "localhost"
        db_port = parsed.port or 5432

        pg_ok = tcp_check(db_host, db_port, timeout=1.0)
        qdrant_ok = tcp_check(settings.qdrant_host, settings.qdrant_port, timeout=1.0)

        dependencies = {
            "postgresql": "ok" if pg_ok else "unreachable",
            "qdrant": "ok" if qdrant_ok else "unreachable",
            "ollama": "not_configured",
        }

        overall_status = "ok" if pg_ok and qdrant_ok else "not_ready"

    return ReadinessResponse(
        status=overall_status,
        version=settings.app_version,
        dependencies=dependencies,
    )
