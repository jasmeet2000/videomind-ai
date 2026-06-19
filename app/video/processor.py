"""
VideoMind AI — Video Processor
===============================
Orchestrates metadata extraction, audio extraction, and frame extraction
into a single, testable entrypoint for the ingestion pipeline.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from app.video.extractor import AudioExtractor
from app.video.frames import FrameExtractor
from app.video.metadata import extract_metadata
from app.core.logging import get_logger
from app.core.exceptions import VideoProcessingError

logger = get_logger(__name__)


class VideoProcessor:
    """Compose AudioExtractor + FrameExtractor + metadata extractor."""

    def __init__(
        self,
        audio_extractor: AudioExtractor | None = None,
        frame_extractor: FrameExtractor | None = None,
        output_dir: str = "./data",
    ) -> None:
        self.audio_extractor = audio_extractor or AudioExtractor()
        self.frame_extractor = frame_extractor or FrameExtractor()
        self.output_dir = Path(output_dir)

    def process(self, video_path: str, video_id: str) -> Dict[str, Any]:
        """Run metadata extraction, audio extraction, and frame sampling.

        Returns a summary dict with keys: video_id, metadata, audio_path, frames
        """
        try:
            metadata = extract_metadata(video_path)

            audio_dir = self.output_dir / "audio"
            audio_dir.mkdir(parents=True, exist_ok=True)
            audio_path = str(audio_dir / f"{video_id}.wav")

            audio_path = self.audio_extractor.extract(video_path, audio_path)

            frames = self.frame_extractor.extract(video_path, video_id)

            summary = {
                "video_id": video_id,
                "metadata": metadata,
                "audio_path": audio_path,
                "frames": frames,
            }

            logger.info("VideoProcessor completed", video_id=video_id, frames=len(frames))
            return summary

        except VideoProcessingError:
            # Preserve domain-specific errors
            raise
        except Exception as exc:  # pragma: no cover - unexpected runtime errors
            logger.exception("Unexpected error in VideoProcessor", error=str(exc))
            raise VideoProcessingError("processor", video_id, str(exc))
