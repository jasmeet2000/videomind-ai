"""
VideoMind AI — Domain Entities
================================
Pure Python dataclasses representing the core business objects.

SOLID Principle — Single Responsibility (SRP):
    Each entity class represents exactly one concept in the domain.
    No entity contains business logic; they are data containers only.

SOLID Principle — Dependency Inversion (DIP):
    All service layers depend on these entities, never the reverse.
    Entities import nothing from this project.

Layer rule: This file may ONLY import from stdlib and third-party packages.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
import uuid

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class VideoStatus(str, Enum):
    """Lifecycle states of a video through the ingestion pipeline."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Modality(str, Enum):
    """Which pipeline produced a given chunk of content."""

    AUDIO = "audio"  # Whisper transcript
    VISUAL = "visual"  # OCR or vision model output
    OBJECT = "object"  # Object detection labels
    SCENE = "scene"  # Scene classification


# ---------------------------------------------------------------------------
# Core Entities
# ---------------------------------------------------------------------------


@dataclass
class Video:
    """
    Represents an uploaded video and its processing metadata.

    Attributes:
        id: Unique identifier (UUID4 string).
        filename: Original uploaded filename.
        file_path: Absolute path to the stored video file.
        duration_seconds: Total video duration.
        fps: Frames per second of the source video.
        resolution: (width, height) tuple.
        codec: Video codec string (e.g., "h264").
        status: Current processing lifecycle status.
        created_at: Timestamp of upload.
        updated_at: Timestamp of last status change.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    filename: str = ""
    file_path: str = ""
    duration_seconds: float = 0.0
    fps: float = 0.0
    resolution: tuple[int, int] = (0, 0)
    codec: str = ""
    status: VideoStatus = VideoStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TranscriptChunk:
    """
    A single timestamped segment from the Whisper speech-to-text output.

    Attributes:
        id: Unique identifier.
        video_id: Foreign key to the parent Video.
        text: Transcribed text content.
        start_seconds: Start timestamp in the video.
        end_seconds: End timestamp in the video.
        confidence: Model confidence score [0.0, 1.0].
        language: Detected language code (e.g., "en").
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    video_id: str = ""
    text: str = ""
    start_seconds: float = 0.0
    end_seconds: float = 0.0
    confidence: float = 0.0
    language: str = "en"


@dataclass
class TextBlock:
    """
    A single block of text extracted by an OCR engine from a video frame.

    SOLID — Liskov Substitution (LSP):
        All OCR engines return List[TextBlock]. The caller never knows
        which engine produced the output.

    Attributes:
        text: Raw OCR-extracted text.
        confidence: OCR confidence score [0.0, 1.0].
        bounding_box: (x, y, width, height) pixel coordinates.
    """

    text: str = ""
    confidence: float = 0.0
    bounding_box: tuple[int, int, int, int] = (0, 0, 0, 0)


@dataclass
class Frame:
    """
    Represents a single extracted video frame with all annotations.

    Attributes:
        id: Unique identifier.
        video_id: Foreign key to the parent Video.
        timestamp_seconds: Position in the video where frame was captured.
        file_path: Path to the saved frame image file.
        ocr_blocks: List of TextBlocks extracted by OCR.
        objects_detected: List of detected object label strings.
        scene_label: High-level scene classification (e.g., "whiteboard").
        description: Vision model description of the frame content.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    video_id: str = ""
    timestamp_seconds: float = 0.0
    file_path: str = ""
    ocr_blocks: list[TextBlock] = field(default_factory=list)
    objects_detected: list[str] = field(default_factory=list)
    scene_label: str = ""
    description: str = ""


@dataclass
class SearchResult:
    """
    A single retrieved chunk returned by the retrieval pipeline.

    Attributes:
        chunk_id: ID of the retrieved TranscriptChunk or Frame.
        video_id: Parent video identifier.
        modality: Which pipeline produced this chunk.
        text: The text content of this chunk.
        score: Relevance score from the retriever [0.0, 1.0].
        start_seconds: Timestamp in the video.
        end_seconds: End timestamp (None for frame results).
        metadata: Arbitrary extra metadata dict.
    """

    chunk_id: str = ""
    video_id: str = ""
    modality: Modality = Modality.AUDIO
    text: str = ""
    score: float = 0.0
    start_seconds: float = 0.0
    end_seconds: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineEvent:
    """
    Observer pattern — emitted by each pipeline stage for monitoring.

    DESIGN PATTERN — Observer:
        Services emit PipelineEvents instead of embedding timing/monitoring
        logic inline. The event bus (core/events.py) fans these out to
        registered handlers (logging, metrics, alerting) without coupling
        the service to any specific monitoring tool.

    Attributes:
        stage: Name of the pipeline stage (e.g., "whisper_transcription").
        video_id: The video being processed.
        duration_ms: How long this stage took in milliseconds.
        success: Whether the stage completed without error.
        error_message: Populated only when success=False.
        metadata: Additional key-value pairs for the event.
    """

    stage: str = ""
    video_id: str = ""
    duration_ms: float = 0.0
    success: bool = True
    error_message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
