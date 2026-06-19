"""
VideoMind AI — Object Detector
================================
Detects objects in video frames using a torchvision model.

SOLID — Single Responsibility:
    Detects objects only. Scene classification is in scene_analyzer.py.
"""

from __future__ import annotations

import numpy as np

from app.core.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Optional heavy dependencies — imported at module level so they can be
# patched cleanly in unit tests.  A missing library simply leaves the names
# as None; the init guard in _init_model() handles that gracefully.
# ---------------------------------------------------------------------------
try:
    from PIL import Image
    import torch
    from torchvision.transforms import functional as F
except ImportError:  # pragma: no cover
    torch = None  # type: ignore[assignment]
    Image = None  # type: ignore[assignment]
    F = None  # type: ignore[assignment]


class ObjectDetector:
    """Detects objects in a video frame and returns label strings."""

    def __init__(self, confidence_threshold: float = 0.5) -> None:
        """
        Initialize ObjectDetector config.
        """
        self.confidence_threshold = confidence_threshold
        self._model = None
        self._categories = None

    def _init_model(self) -> None:
        """
        Lazily initialize the detection model and category names.
        """
        if self._model is None:
            try:
                from torchvision.models.detection import (
                    SSDLite320_MobileNet_V3_Large_Weights,
                    ssdlite320_mobilenet_v3_large,
                )

                # Use SSDLite MobileNet V3 Large which is lightweight and fast on CPU
                weights = SSDLite320_MobileNet_V3_Large_Weights.DEFAULT
                self._model = ssdlite320_mobilenet_v3_large(weights=weights)
                self._model.eval()
                self._categories = weights.meta["categories"]
            except Exception as exc:
                logger.error("Failed to initialize ObjectDetector model", error=str(exc))
                self._model = False

    def detect(self, image: np.ndarray) -> list[str]:
        """
        Detect objects in a BGR image array.

        Args:
            image: BGR image array (H x W x 3) from OpenCV.

        Returns:
            List of detected object label strings (e.g., ["person", "laptop"]).
        """
        self._init_model()
        if not self._model or self._categories is None:
            return []

        try:
            # Convert OpenCV BGR to PIL RGB
            rgb_image = Image.fromarray(image[:, :, ::-1])

            # Transform to tensor
            tensor_image = F.to_tensor(rgb_image).unsqueeze(0)

            # Inference
            with torch.no_grad():
                predictions = self._model(tensor_image)

            if not predictions:
                return []

            pred = predictions[0]
            scores = pred["scores"].tolist()
            labels = pred["labels"].tolist()

            detected_labels = []
            for score, label_idx in zip(scores, labels):
                if score >= self.confidence_threshold and 0 <= label_idx < len(self._categories):
                    detected_labels.append(self._categories[label_idx])

            # Deduplicate labels
            return list(set(detected_labels))

        except Exception as exc:
            logger.error("Object detection inference failed", error=str(exc))
            return []
