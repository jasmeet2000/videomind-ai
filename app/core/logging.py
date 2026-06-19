"""
VideoMind AI — Structured Logging Setup
=========================================
Configures Loguru as the project-wide logging solution.

12-Factor App — Logs as event streams:
    Logs are written to stdout (not files) in structured JSON format.
    A separate Loguru sink can also write to ./logs/ for local dev.

SOLID — Single Responsibility:
    This module only configures and exposes the logger.
    It never performs any other work.

Usage:
    from app.core.logging import get_logger
    logger = get_logger(__name__)
    logger.info("Processing started", video_id=video_id)
"""

from __future__ import annotations

import sys

from loguru import logger as _loguru_logger

from app.core.config import get_settings


def configure_logging() -> None:
    """
    Remove Loguru defaults and configure structured JSON output to stdout.
    Call once at application startup (in app/main.py lifespan).

    Production: JSON to stdout (captured by Docker/log aggregator).
    Development: Human-readable colored output to stdout.
    """
    settings = get_settings()

    # Remove default Loguru handler
    _loguru_logger.remove()

    if settings.debug:
        # Human-readable format for local development
        _loguru_logger.add(
            sys.stdout,
            level=settings.log_level,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{line}</cyan> | "
                "{message}"
            ),
            colorize=True,
        )
    else:
        # Structured JSON for production (parseable by log aggregators)
        _loguru_logger.add(
            sys.stdout,
            level=settings.log_level,
            serialize=True,  # Emit JSON lines
        )


def get_logger(name: str):
    """
    Return a contextualized logger bound to the given module name.

    Args:
        name: Typically __name__ of the calling module.

    Returns:
        A Loguru logger instance bound with the module name.
    """
    return _loguru_logger.bind(module=name)
