"""
VideoMind AI — Object Detector
================================
Detects objects in video frames using a YOLO or torchvision model.

SOLID — Single Responsibility:
    Detects objects only. Scene classification is in scene_analyzer.py.
"""

from __future__ import annotations

import numpy as np

# Stub — implementation in Phase 5


class ObjectDetector:
    """Detects objects in a video frame and returns label strings."""

    def detect(self, image: np.ndarray) -> list[str]:
        """
        Detect objects in a BGR image array.

        Args:
            image: BGR image array (H x W x 3) from OpenCV.

        Returns:
            List of detected object label strings (e.g., ["person", "laptop"]).
        """
        raise NotImplementedError("Phase 5: Implement YOLO object detection")
