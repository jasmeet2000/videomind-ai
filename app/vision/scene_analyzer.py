"""
VideoMind AI — Scene Analyzer
================================
Classifies the scene depicted in a video frame (e.g., "whiteboard",
"code editor", "presentation slide", "outdoor").

SOLID — Single Responsibility:
    Scene classification only. Object detection is in object_detector.py.
"""

from __future__ import annotations

import numpy as np

# Stub — implementation in Phase 5


class SceneAnalyzer:
    """Classifies the high-level scene of a video frame."""

    def classify(self, image: np.ndarray) -> str:
        """
        Classify the scene type of a BGR image frame.

        Args:
            image: BGR image array (H x W x 3) from OpenCV.

        Returns:
            Scene label string (e.g., "whiteboard", "slide", "outdoor").
        """
        raise NotImplementedError("Phase 5: Implement scene classification")
