"""
VideoMind AI — Frame Extractor
================================
Samples video frames at a configurable rate using OpenCV, saves them
as JPEG images, and returns Frame entity objects with timestamps.

SOLID — Single Responsibility:
    Only extracts and saves frames. Does not run OCR, object detection,
    or save to a database.

SOLID — Dependency Inversion:
    Accepts configuration via constructor injection (sample_rate_fps),
    not by reading global state.

DESIGN PATTERN — Composition:
    VideoProcessor composes FrameExtractor + AudioExtractor, rather than
    inheriting from a base extractor class.
"""

from __future__ import annotations

from pathlib import Path

from app.core.constants import DEFAULT_FRAME_SAMPLE_RATE_FPS, FRAME_IMAGE_FORMAT, FRAME_JPEG_QUALITY
from app.core.exceptions import FrameExtractionError
from app.core.logging import get_logger
from app.domain.entities import Frame

logger = get_logger(__name__)


class FrameExtractor:
    """
    Extracts frames from a video file at a given sample rate using OpenCV.
    """

    def __init__(self, sample_rate_fps: float = 1.0, output_dir: str = "./data/frames") -> None:
        """
        Args:
            sample_rate_fps: Number of frames to extract per second of video.
            output_dir: Directory where frame JPEG files will be saved.
        """
        self.sample_rate_fps = sample_rate_fps
        self.output_dir = output_dir

    def extract(self, video_path: str, video_id: str) -> list[Frame]:
        """
        Extract frames from a video and return Frame entities.

        This implementation attempts to use OpenCV. If OpenCV is not
        available or the video cannot be opened, a FrameExtractionError
        is raised.
        """
        try:
            import cv2
        except Exception as exc:
            raise FrameExtractionError(video_id, f"OpenCV not available: {exc}")

        src = Path(video_path)
        if not src.exists():
            raise FrameExtractionError(video_id, "source file not found")

        cap = cv2.VideoCapture(str(src))
        if not cap.isOpened():
            raise FrameExtractionError(video_id, "cannot open video file")

        fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        duration = (frame_count / fps) if fps > 0 else 0.0

        sample_rate = (
            self.sample_rate_fps if self.sample_rate_fps > 0 else DEFAULT_FRAME_SAMPLE_RATE_FPS
        )

        out_dir = Path(self.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        frames: list[Frame] = []
        t = 0.0
        max_iter = max(1, int(duration * sample_rate) + 5)

        for i in range(max_iter):
            frame_no = int(round(t * fps)) if fps > 0 else i

            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
            ret, img = cap.read()
            if not ret:
                break

            timestamp_seconds = (frame_no / fps) if fps > 0 else t
            filename = f"{video_id}_frame_{int(timestamp_seconds * 1000)}.{FRAME_IMAGE_FORMAT}"
            file_path = out_dir / filename

            try:
                cv2.imwrite(
                    str(file_path), img, [int(cv2.IMWRITE_JPEG_QUALITY), FRAME_JPEG_QUALITY]
                )
            except Exception as write_exc:
                logger.warning("Failed to write frame image", error=str(write_exc))

            frames.append(
                Frame(
                    video_id=video_id,
                    timestamp_seconds=timestamp_seconds,
                    file_path=str(file_path),
                )
            )

            t += 1.0 / sample_rate

        cap.release()
        return frames
