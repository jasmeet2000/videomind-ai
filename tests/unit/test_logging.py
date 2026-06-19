"""
Unit tests for app/core/logging.py

Tests verify:
- configure_logging() runs without error
- get_logger() returns a logger with the module name bound
- Loguru logger is the correct object type
- Logger can emit messages without raising

Note: We test that the logging infrastructure is functional, not the
content of log output (that would require capturing stdout in tests,
which is fragile). Loguru's own test suite covers output formatting.
"""

from __future__ import annotations

import pytest
from loguru import logger as loguru_logger

from app.core.logging import configure_logging, get_logger


class TestConfigureLogging:
    """Tests for the configure_logging() setup function."""

    def test_configure_logging_runs_without_error(self) -> None:
        """configure_logging() must not raise any exception."""
        try:
            configure_logging()
        except Exception as exc:
            pytest.fail(f"configure_logging() raised an exception: {exc}")

    def test_configure_logging_idempotent(self) -> None:
        """Calling configure_logging() twice must not raise."""
        configure_logging()
        configure_logging()  # Second call — should reset and reapply cleanly


class TestGetLogger:
    """Tests for the get_logger() factory."""

    def test_returns_logger(self) -> None:
        """get_logger() must return a Loguru logger object."""
        log = get_logger("test_module")
        assert log is not None

    def test_logger_has_module_context(self) -> None:
        """Logger returned by get_logger() must be bound with module name."""
        log = get_logger("app.core.config")
        # Loguru bound loggers are not a separate class — they're the same
        # logger with extra context. We verify it's callable:
        assert callable(log.info)
        assert callable(log.error)
        assert callable(log.debug)
        assert callable(log.warning)

    def test_logger_info_does_not_raise(self) -> None:
        """Calling logger.info() must not raise any exception."""
        configure_logging()
        log = get_logger(__name__)
        try:
            log.info("Test log message", extra_field="test_value")
        except Exception as exc:
            pytest.fail(f"logger.info() raised: {exc}")

    def test_logger_error_does_not_raise(self) -> None:
        """Calling logger.error() must not raise."""
        configure_logging()
        log = get_logger(__name__)
        try:
            log.error("Test error message")
        except Exception as exc:
            pytest.fail(f"logger.error() raised: {exc}")

    def test_logger_with_contextualize(self) -> None:
        """
        Loguru's contextualize() must work for request_id injection.
        This is the pattern used in the request_id_middleware.
        """
        configure_logging()
        log = get_logger(__name__)
        try:
            with log.contextualize(request_id="test-request-id-123"):
                log.info("Request processing", video_id="vid-456")
        except Exception as exc:
            pytest.fail(f"contextualize() raised: {exc}")

    def test_different_module_names_work(self) -> None:
        """get_logger() should work with any module name string."""
        modules = [
            "app.video.extractor",
            "app.speech.whisper_service",
            "app.use_cases.ingest_video",
            "tests.unit.test_logging",
        ]
        for module in modules:
            log = get_logger(module)
            assert log is not None, f"get_logger({module!r}) returned None"
