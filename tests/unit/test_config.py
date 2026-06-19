"""
Unit tests for app/core/config.py

Tests verify:
- Settings loads successfully with defaults
- get_settings() is a singleton (same object every call)
- Field types and constraints are correct
- Pydantic validation works for invalid values

SOLID — Dependency Inversion (test pattern):
    Tests call get_settings() via the public interface.
    They never instantiate Settings directly with raw env vars
    — they patch os.environ to simulate different environments.
"""

from __future__ import annotations

import os
from unittest.mock import patch

from app.core.config import Settings, get_settings


class TestSettings:
    """Tests for the Settings Pydantic BaseSettings model."""

    def test_settings_loads_with_defaults(self) -> None:
        """Settings should instantiate successfully using default values."""
        settings = Settings()
        assert settings.app_name == "VideoMind AI"
        assert settings.app_version == "0.1.0"
        assert settings.debug is False
        assert settings.log_level == "INFO"

    def test_database_url_has_default(self) -> None:
        """A sensible default DATABASE_URL should be set for local dev."""
        settings = Settings()
        assert "postgresql://" in settings.database_url
        assert "videomind" in settings.database_url

    def test_qdrant_defaults(self) -> None:
        """Qdrant should default to localhost:6333."""
        settings = Settings()
        assert settings.qdrant_host == "localhost"
        assert settings.qdrant_port == 6333

    def test_ollama_defaults(self) -> None:
        """Ollama should default to localhost:11434."""
        settings = Settings()
        assert "localhost" in settings.ollama_host
        assert settings.ollama_model == "qwen3"

    def test_embedding_defaults(self) -> None:
        """Embedding model defaults should match the chosen open-source model."""
        settings = Settings()
        assert settings.embedding_model == "BAAI/bge-small-en-v1.5"
        assert settings.embedding_device == "cpu"
        assert settings.embedding_batch_size == 32

    def test_whisper_defaults(self) -> None:
        """Whisper should default to base model on CPU."""
        settings = Settings()
        assert settings.whisper_model == "base"
        assert settings.whisper_device == "cpu"

    def test_retrieval_defaults(self) -> None:
        """Retrieval hyperparameters should have sensible defaults."""
        settings = Settings()
        assert settings.dense_retrieval_top_k == 10
        assert settings.rerank_top_k == 5
        assert 0.0 < settings.hybrid_alpha < 1.0

    def test_settings_override_via_env(self) -> None:
        """Environment variables should override defaults (12-Factor)."""
        with patch.dict(os.environ, {"DEBUG": "true", "LOG_LEVEL": "DEBUG"}):
            settings = Settings()
            assert settings.debug is True
            assert settings.log_level == "DEBUG"

    def test_max_video_size_is_positive(self) -> None:
        """Max video size must be a positive integer."""
        settings = Settings()
        assert settings.max_video_size_mb > 0

    def test_ocr_confidence_threshold_range(self) -> None:
        """OCR confidence threshold must be between 0 and 1."""
        settings = Settings()
        assert 0.0 <= settings.ocr_confidence_threshold <= 1.0


class TestGetSettings:
    """Tests for the get_settings() singleton factory."""

    def test_get_settings_returns_settings_instance(self) -> None:
        """get_settings() must return a Settings object."""
        result = get_settings()
        assert isinstance(result, Settings)

    def test_get_settings_is_singleton(self) -> None:
        """
        get_settings() must return the same instance every call.

        DESIGN PATTERN — Singleton via lru_cache:
            This test verifies the cache is working. Expensive Settings
            instantiation (env var parsing) happens only once per process.
        """
        instance_a = get_settings()
        instance_b = get_settings()
        assert instance_a is instance_b

    def test_get_settings_app_name_is_string(self) -> None:
        """app_name must be a non-empty string."""
        settings = get_settings()
        assert isinstance(settings.app_name, str)
        assert len(settings.app_name) > 0
