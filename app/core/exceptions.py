"""
VideoMind AI — Custom Domain Exceptions
=========================================
Defines a hierarchy of custom exceptions, one per domain area.

SOLID — Single Responsibility:
    Each exception class represents exactly one error category.
    No catch-all base classes that swallow context.

Fail Fast principle:
    Exceptions are raised as early as possible (e.g., invalid video format
    is detected at upload time, not during processing).

Production requirement:
    FastAPI exception handlers (registered in main.py) catch these and
    return structured JSON error responses. Stack traces NEVER reach clients.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Base exception
# ---------------------------------------------------------------------------

class VideoMindError(Exception):
    """
    Root exception for all VideoMind AI errors.
    Carry a human-readable message and an optional HTTP status code hint.
    """

    def __init__(self, message: str, status_code: int = 500) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


# ---------------------------------------------------------------------------
# Video processing exceptions
# ---------------------------------------------------------------------------

class VideoNotFoundError(VideoMindError):
    """Raised when a requested video ID does not exist in the database."""

    def __init__(self, video_id: str) -> None:
        super().__init__(f"Video '{video_id}' not found.", status_code=404)
        self.video_id = video_id


class InvalidVideoFormatError(VideoMindError):
    """
    Raised immediately on upload if the file format is unsupported.
    Fail Fast: we reject bad input before any pipeline work starts.
    """

    def __init__(self, filename: str, reason: str) -> None:
        super().__init__(
            f"Invalid video file '{filename}': {reason}",
            status_code=422,
        )


class VideoProcessingError(VideoMindError):
    """Raised when a pipeline stage fails during video ingestion."""

    def __init__(self, stage: str, video_id: str, reason: str) -> None:
        super().__init__(
            f"Pipeline stage '{stage}' failed for video '{video_id}': {reason}",
            status_code=500,
        )
        self.stage = stage
        self.video_id = video_id


# ---------------------------------------------------------------------------
# Speech pipeline exceptions
# ---------------------------------------------------------------------------

class TranscriptionError(VideoMindError):
    """Raised when Whisper fails to transcribe audio."""

    def __init__(self, video_id: str, reason: str) -> None:
        super().__init__(
            f"Transcription failed for video '{video_id}': {reason}",
            status_code=500,
        )


# ---------------------------------------------------------------------------
# OCR / Vision exceptions
# ---------------------------------------------------------------------------

class OCREngineUnavailableError(VideoMindError):
    """Raised when neither PaddleOCR nor EasyOCR is available."""

    def __init__(self) -> None:
        super().__init__("No OCR engine is available.", status_code=503)


class FrameExtractionError(VideoMindError):
    """Raised when OpenCV fails to extract frames from a video."""

    def __init__(self, video_id: str, reason: str) -> None:
        super().__init__(
            f"Frame extraction failed for video '{video_id}': {reason}",
            status_code=500,
        )


# ---------------------------------------------------------------------------
# Embedding exceptions
# ---------------------------------------------------------------------------

class EmbeddingModelNotFoundError(VideoMindError):
    """Raised when a requested embedding model is not registered."""

    def __init__(self, model_name: str) -> None:
        super().__init__(
            f"Embedding model '{model_name}' is not registered.",
            status_code=500,
        )


# ---------------------------------------------------------------------------
# Retrieval exceptions
# ---------------------------------------------------------------------------

class VectorSearchError(VideoMindError):
    """Raised when the Qdrant search operation fails."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"Vector search failed: {reason}", status_code=503)


# ---------------------------------------------------------------------------
# LLM / Generation exceptions
# ---------------------------------------------------------------------------

class LLMUnavailableError(VideoMindError):
    """Raised when Ollama is unreachable or returns an error."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"LLM backend unavailable: {reason}", status_code=503)


class PromptBuildError(VideoMindError):
    """Raised when the PromptBuilder cannot assemble a valid prompt."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"Prompt construction failed: {reason}", status_code=500)


# ---------------------------------------------------------------------------
# Configuration exceptions
# ---------------------------------------------------------------------------

class ConfigurationError(VideoMindError):
    """Raised when a required environment variable is missing or invalid."""

    def __init__(self, variable: str, reason: str) -> None:
        super().__init__(
            f"Configuration error for '{variable}': {reason}",
            status_code=500,
        )
