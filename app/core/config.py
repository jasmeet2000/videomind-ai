"""
VideoMind AI — Core Configuration
====================================
Loads all settings from environment variables using Pydantic BaseSettings.

12-Factor App — Config:
    All configuration lives in environment variables, never in source code.
    A single .env file is used for local development; Docker Compose
    injects the same vars in production.

SOLID — Single Responsibility:
    This module only handles configuration. It does not start services.

DESIGN PATTERN — Singleton (via @lru_cache):
    get_settings() is called throughout the app but only instantiates
    Settings once. All consumers share the same object.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application-wide configuration loaded from environment variables.
    All fields have sensible defaults for local development.
    """

    # --- Application ---
    app_name: str = Field(default="VideoMind AI", description="Human-readable app name.")
    app_version: str = Field(default="0.1.0", description="Semantic version string.")
    debug: bool = Field(default=False, description="Enable debug mode (never True in prod).")
    log_level: str = Field(default="INFO", description="Loguru log level.")

    # --- Database ---
    database_url: str = Field(
        default="postgresql://videomind:videomind@localhost:5432/videomind",
        description="Full PostgreSQL connection string.",
    )

    # --- Vector Database ---
    qdrant_host: str = Field(default="localhost")
    qdrant_port: int = Field(default=6333)
    qdrant_collection_name: str = Field(default="videomind")

    # --- LLM ---
    ollama_host: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="qwen3")
    ollama_timeout_seconds: int = Field(default=120)

    # --- Embedding ---
    embedding_model: str = Field(default="BAAI/bge-small-en-v1.5")
    embedding_batch_size: int = Field(default=32)
    embedding_device: str = Field(default="cpu")

    # --- Speech-to-Text ---
    whisper_model: str = Field(default="base")
    whisper_device: str = Field(default="cpu")
    whisper_language: str = Field(default="auto")

    # --- Video Processing ---
    data_dir: str = Field(default="./data")
    max_video_size_mb: int = Field(default=500)
    frame_sample_rate_fps: float = Field(default=1.0)
    ffmpeg_path: str = Field(default="ffmpeg")

    # --- OCR ---
    ocr_engine: str = Field(default="paddleocr")
    ocr_confidence_threshold: float = Field(default=0.7)

    # --- Readiness checks ---
    # When true, /health/ready performs TCP connectivity checks to DB and Qdrant.
    check_readiness: bool = Field(default=False, description="Enable readiness connectivity checks (used in Phase 6/CI)")

    # --- Retrieval ---
    dense_retrieval_top_k: int = Field(default=10)
    rerank_top_k: int = Field(default=5)
    hybrid_alpha: float = Field(default=0.7, description="Weight for dense vs sparse (0=sparse, 1=dense).")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",          # Ignore extra env vars (12-Factor: permissive)
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the singleton Settings instance.

    DESIGN PATTERN — Singleton via lru_cache:
        lru_cache with maxsize=1 ensures Settings is instantiated exactly
        once per process. All callers share the same object without
        global state or class-level mutation.

    Returns:
        The application Settings instance.
    """
    return Settings()
