"""
VideoMind AI — Audio Extractor
================================
Extracts audio from a video file using FFmpeg and saves it as a
16 kHz mono WAV file suitable for Whisper transcription.

SOLID — Single Responsibility:
    Extracts audio only. Does not transcribe, does not save metadata.

SOLID — Dependency Inversion:
    Depends on the ffmpeg-python wrapper. The path to ffmpeg binary
    is injected via Settings (never hardcoded).

YAGNI:
    Does not implement streaming audio extraction — batch extraction
    is sufficient for the current use case.
"""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

from app.core.exceptions import VideoProcessingError
from app.core.logging import get_logger

logger = get_logger(__name__)


class AudioExtractor:
    """
    Extracts audio track from a video file using FFmpeg.

    Composition target: VideoProcessor composes AudioExtractor +
    FrameExtractor + MetadataExtractor (Composition over inheritance).
    """

    def __init__(self, ffmpeg_path: str = "ffmpeg") -> None:
        """
        Args:
            ffmpeg_path: Path to the ffmpeg binary.
        """
        self.ffmpeg_path = ffmpeg_path

    def extract(self, video_path: str, output_path: str) -> str:
        """
        Extract audio from video and save as 16 kHz mono WAV.

        Args:
            video_path: Path to the source video file.
            output_path: Path where the WAV file will be written.

        Returns:
            Absolute path to the extracted audio WAV file.

        Raises:
            VideoProcessingError: If FFmpeg extraction fails.
        """
        src = Path(video_path)
        dst = Path(output_path)

        if not src.exists():
            raise VideoProcessingError("audio_extraction", video_path, "source file not found")

        dst.parent.mkdir(parents=True, exist_ok=True)

        # Resolve ffmpeg binary
        ffmpeg_bin = shutil.which(self.ffmpeg_path) or (self.ffmpeg_path if Path(self.ffmpeg_path).exists() else None)
        if not ffmpeg_bin:
            raise VideoProcessingError("audio_extraction", video_path, f"ffmpeg not found at '{self.ffmpeg_path}'")

        cmd = [ffmpeg_bin, "-y", "-i", str(src), "-ac", "1", "-ar", "16000", "-vn", "-f", "wav", str(dst)]

        try:
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode != 0:
                stderr = (proc.stderr or "").strip()
                logger.error("ffmpeg failed", stderr=stderr)
                raise VideoProcessingError("audio_extraction", video_path, f"ffmpeg failed: {stderr}")
        except Exception as exc:  # pragma: no cover - runtime/IO failures
            raise VideoProcessingError("audio_extraction", video_path, f"ffmpeg execution error: {exc}")

        return str(dst.resolve())
