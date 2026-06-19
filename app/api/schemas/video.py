"""
VideoMind AI — Video API Schemas (Phase 2)
===========================================
Pydantic v2 request and response models for the video upload and status API.

SOLID — Single Responsibility:
    Schemas only define data shapes and validation rules.
    No business logic, no DB calls.

Production requirement:
    Pydantic v2 validates all inputs at the API boundary (Fail Fast).
    Invalid requests are rejected before reaching the use case layer.
"""

from __future__ import annotations

from datetime import datetime
from typing import Tuple

from pydantic import BaseModel, Field

from app.domain.entities import VideoStatus

# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class UploadVideoRequest(BaseModel):
    """
    Metadata accompanying a video file upload (multipart form).

    The actual file bytes come via FastAPI's UploadFile — this schema
    captures any additional metadata fields sent with the form.
    """
    title: str | None = Field(
        default=None,
        max_length=255,
        description="Optional human-readable title for the video.",
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional freeform description of the video content.",
    )


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class VideoMetadataResponse(BaseModel):
    """
    Technical and processing metadata returned after upload or status check.
    """
    id: str = Field(description="Unique video identifier (UUID4).")
    filename: str = Field(description="Original uploaded filename.")
    status: VideoStatus = Field(description="Current processing lifecycle status.")
    duration_seconds: float = Field(default=0.0, description="Video duration in seconds.")
    fps: float = Field(default=0.0, description="Frames per second of the source video.")
    resolution: Tuple[int, int] = Field(
        default=(0, 0),
        description="Video resolution as (width, height) in pixels.",
    )
    codec: str = Field(default="", description="Video codec identifier (e.g., 'h264').")
    created_at: datetime = Field(description="UTC timestamp of initial upload.")
    updated_at: datetime = Field(description="UTC timestamp of last status change.")

    model_config = {"from_attributes": True}


class UploadVideoResponse(BaseModel):
    """Response returned immediately after a successful video upload."""
    video_id: str = Field(description="Unique ID assigned to the uploaded video.")
    status: VideoStatus = Field(description="Initial processing status (always PENDING).")
    message: str = Field(
        default="Video accepted for processing.",
        description="Human-readable status message.",
    )


class VideoStatusResponse(BaseModel):
    """Response for polling the processing status of an uploaded video."""
    video_id: str
    status: VideoStatus
    progress_message: str = Field(
        default="",
        description="Human-readable description of current processing stage.",
    )


class ErrorResponse(BaseModel):
    """
    Standardized error response returned by all exception handlers.

    Production requirement: clients always receive this shape on error —
    never a raw Python exception or stack trace.
    """
    error: str = Field(description="Exception class name (e.g., 'VideoNotFoundError').")
    message: str = Field(description="Human-readable error description.")
    request_id: str = Field(description="Unique request ID for log correlation.")
