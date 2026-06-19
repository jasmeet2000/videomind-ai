"""
Unit tests for the FastAPI application — health endpoints (Phase 2)

Tests verify:
- GET /health returns 200 with correct schema
- GET /health/ready returns 200 with dependency statuses
- Request-ID is attached to every response header
- Domain exceptions return structured JSON (not stack traces)
- Unhandled exceptions return 500 with structured JSON

Uses FastAPI's TestClient (httpx-based) for in-process testing.
No external services required — all Phase 2 tests run without Docker.

Clean Architecture — API Layer testing:
    We test at the HTTP boundary. Route handlers call use cases;
    use cases are mocked. This ensures routes are wired correctly
    without running the full pipeline.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.exceptions import VideoNotFoundError
from app.main import create_app


@pytest.fixture()
def client() -> TestClient:
    """
    Create a fresh FastAPI TestClient for each test.

    DESIGN PATTERN — Factory (test pattern):
        create_app() is called per test so each test gets an isolated
        application instance with no shared state.
    """
    app = create_app()
    return TestClient(app, raise_server_exceptions=False)


class TestHealthEndpoint:
    """Tests for GET /health (liveness probe)."""

    def test_health_returns_200(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_has_status_ok(self, client: TestClient) -> None:
        response = client.get("/health")
        body = response.json()
        assert body["status"] == "ok"

    def test_health_response_has_version(self, client: TestClient) -> None:
        response = client.get("/health")
        body = response.json()
        assert "version" in body
        assert isinstance(body["version"], str)
        assert len(body["version"]) > 0

    def test_health_response_has_app_name(self, client: TestClient) -> None:
        response = client.get("/health")
        body = response.json()
        assert "app_name" in body
        assert "VideoMind" in body["app_name"]

    def test_health_response_is_json(self, client: TestClient) -> None:
        response = client.get("/health")
        assert "application/json" in response.headers["content-type"]

    def test_health_attaches_request_id_header(self, client: TestClient) -> None:
        """
        Production requirement: every response must carry X-Request-ID.
        This enables log correlation across distributed systems.
        """
        response = client.get("/health")
        assert "x-request-id" in response.headers
        assert len(response.headers["x-request-id"]) > 0

    def test_health_request_id_is_uuid_format(self, client: TestClient) -> None:
        import uuid
        response = client.get("/health")
        request_id = response.headers["x-request-id"]
        # Should not raise ValueError if it's a valid UUID
        parsed = uuid.UUID(request_id)
        assert str(parsed) == request_id


class TestReadinessEndpoint:
    """Tests for GET /health/ready (readiness probe)."""

    def test_readiness_returns_200(self, client: TestClient) -> None:
        response = client.get("/health/ready")
        assert response.status_code == 200

    def test_readiness_response_has_status(self, client: TestClient) -> None:
        body = client.get("/health/ready").json()
        assert "status" in body

    def test_readiness_response_has_dependencies(self, client: TestClient) -> None:
        """Dependencies dict must be present (values are stubs in Phase 2)."""
        body = client.get("/health/ready").json()
        assert "dependencies" in body
        assert isinstance(body["dependencies"], dict)

    def test_readiness_dependency_keys_present(self, client: TestClient) -> None:
        body = client.get("/health/ready").json()
        deps = body["dependencies"]
        assert "postgresql" in deps
        assert "qdrant" in deps
        assert "ollama" in deps

    def test_readiness_attaches_request_id(self, client: TestClient) -> None:
        response = client.get("/health/ready")
        assert "x-request-id" in response.headers

    def test_each_request_gets_unique_id(self, client: TestClient) -> None:
        """Two requests must receive different request IDs."""
        r1 = client.get("/health")
        r2 = client.get("/health")
        assert r1.headers["x-request-id"] != r2.headers["x-request-id"]


class TestExceptionHandlers:
    """Tests for global exception handlers — production requirement."""

    def test_domain_exception_returns_structured_json(self, client: TestClient) -> None:
        """
        VideoMindError must never expose a stack trace.
        The response must always be structured JSON.
        """
        app = create_app()

        @app.get("/test/domain-error")
        async def trigger_domain_error():
            raise VideoNotFoundError("test-video-id")

        test_client = TestClient(app, raise_server_exceptions=False)
        response = test_client.get("/test/domain-error")

        assert response.status_code == 404
        body = response.json()
        assert "error" in body
        assert "message" in body
        assert "request_id" in body
        # Confirm no stack trace in response
        assert "Traceback" not in str(body)
        assert "traceback" not in str(body)

    def test_domain_exception_message_is_human_readable(
        self, client: TestClient
    ) -> None:
        app = create_app()

        @app.get("/test/not-found")
        async def trigger_not_found():
            raise VideoNotFoundError("vid-abc")

        tc = TestClient(app, raise_server_exceptions=False)
        body = tc.get("/test/not-found").json()
        assert "vid-abc" in body["message"]

    def test_unhandled_exception_returns_500_json(self, client: TestClient) -> None:
        """Unexpected exceptions must return 500, not expose stack traces."""
        app = create_app()

        @app.get("/test/unhandled")
        async def trigger_unhandled():
            raise RuntimeError("something completely unexpected")

        tc = TestClient(app, raise_server_exceptions=False)
        response = tc.get("/test/unhandled")

        assert response.status_code == 500
        body = response.json()
        assert "error" in body
        assert "message" in body
        assert "request_id" in body
        # Critical: stack trace must NOT appear in the response body
        assert "RuntimeError" not in body.get("message", "")
        assert "Traceback" not in str(body)


class TestOpenAPISpec:
    """Verify the OpenAPI schema is generated correctly."""

    def test_openapi_json_endpoint_accessible(self, client: TestClient) -> None:
        response = client.get("/openapi.json")
        assert response.status_code == 200

    def test_openapi_has_health_route(self, client: TestClient) -> None:
        spec = client.get("/openapi.json").json()
        paths = spec.get("paths", {})
        assert "/health" in paths

    def test_openapi_has_readiness_route(self, client: TestClient) -> None:
        spec = client.get("/openapi.json").json()
        paths = spec.get("paths", {})
        assert "/health/ready" in paths

    def test_docs_endpoint_accessible(self, client: TestClient) -> None:
        response = client.get("/docs")
        assert response.status_code == 200
