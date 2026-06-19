"""
VideoMind AI — Video Metadata Extractor
=========================================
Extracts technical metadata (duration, FPS, resolution, codec) from a
video file using FFmpeg/OpenCV without loading the full video into memory.

SOLID — Single Responsibility:
    This module does exactly one thing: extract metadata.
    It does not save to a database, emit events, or process frames.

SOLID — Dependency Inversion:
    Accepts a file path string; does not depend on any repository or
    database client. Callers handle persistence.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

from app.core.exceptions import VideoProcessingError
from app.core.logging import get_logger

logger = get_logger(__name__)


def extract_metadata(file_path: str) -> dict:
    """
    Extract technical metadata from a video file using ffprobe (preferred)
    and falling back to OpenCV when ffprobe is unavailable.

    Returns a dict with keys: duration_seconds, fps, width, height, codec.
    """
    src = Path(file_path)
    if not src.exists():
        raise VideoProcessingError("metadata_extraction", file_path, "file not found")

    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        cmd = [ffprobe, "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(src)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            stderr = (proc.stderr or "").strip()
            raise VideoProcessingError("metadata_extraction", file_path, f"ffprobe failed: {stderr}")
        try:
            data = json.loads(proc.stdout)
        except Exception as e:
            raise VideoProcessingError("metadata_extraction", file_path, f"ffprobe parse error: {e}")

        video_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
        duration = float(data.get("format", {}).get("duration") or 0.0)
        fps = 0.0
        width = 0
        height = 0
        codec = ""

        if video_stream:
            avg_frame_rate = video_stream.get("avg_frame_rate", "0/1")
            try:
                num, den = avg_frame_rate.split("/")
                fps = float(num) / float(den) if float(den) != 0 else 0.0
            except Exception:
                fps = 0.0
            width = int(video_stream.get("width") or 0)
            height = int(video_stream.get("height") or 0)
            codec = video_stream.get("codec_name") or ""

        return {
            "duration_seconds": duration,
            "fps": fps,
            "width": width,
            "height": height,
            "codec": codec,
        }

    # Fallback to OpenCV when ffprobe is not available
    try:
        import cv2
    except Exception as e:
        raise VideoProcessingError("metadata_extraction", file_path, f"ffprobe not available and OpenCV missing: {e}")

    cap = cv2.VideoCapture(str(src))
    if not cap.isOpened():
        raise VideoProcessingError("metadata_extraction", file_path, "cannot open file with OpenCV")

    fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = (frame_count / fps) if fps > 0 else 0.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    codec = ""
    cap.release()

    return {
        "duration_seconds": duration,
        "fps": fps,
        "width": width,
        "height": height,
        "codec": codec,
    }
