"""
VideoMind AI — Scene Analyzer
================================
Classifies the high-level scene depicted in a video frame using a torchvision model.

SOLID — Single Responsibility:
    Scene classification only. Object detection is in object_detector.py.
"""

from __future__ import annotations

import numpy as np

from app.core.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Optional heavy dependencies — imported at module level so they can be
# patched cleanly in unit tests.  Missing libraries leave names as None;
# the init guard in _init_model() handles that gracefully.
# ---------------------------------------------------------------------------
try:
    from PIL import Image
    import torch
    import torch.nn.functional as nn_f
    from torchvision.transforms import functional as F  # noqa: N812
except ImportError:  # pragma: no cover
    torch = None  # type: ignore[assignment]
    nn_f = None  # type: ignore[assignment]
    Image = None  # type: ignore[assignment]
    F = None  # type: ignore[assignment]


class SceneAnalyzer:
    """Classifies the high-level scene of a video frame."""

    def __init__(self) -> None:
        """
        Initialize SceneAnalyzer.
        """
        self._model = None
        self._categories = None

    def _init_model(self) -> None:
        """
        Lazily initialize the MobileNet model and class categories.
        """
        if self._model is None:
            try:
                from torchvision.models import (
                    MobileNet_V3_Small_Weights,
                    mobilenet_v3_small,
                )

                # Use a small MobileNet V3 small (~6MB) for fast local CPU inference
                weights = MobileNet_V3_Small_Weights.DEFAULT
                self._model = mobilenet_v3_small(weights=weights)
                self._model.eval()
                self._categories = weights.meta["categories"]
            except Exception as exc:
                logger.error("Failed to initialize SceneAnalyzer model", error=str(exc))
                self._model = False

    def classify(self, image: np.ndarray) -> str:
        """
        Classify the scene type of a BGR image frame.

        Args:
            image: BGR image array (H x W x 3) from OpenCV.

        Returns:
            Scene label string (e.g., "whiteboard", "presentation slide", "outdoor").
        """
        self._init_model()
        if not self._model or self._categories is None:
            return "unknown"

        try:
            # Convert OpenCV BGR to PIL RGB
            rgb_image = Image.fromarray(image[:, :, ::-1])

            # Standard ImageNet pre-processing
            resized = F.resize(rgb_image, [224, 224])
            tensor_img = F.to_tensor(resized)
            normalized = F.normalize(
                tensor_img,
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            )
            batch_tensor = normalized.unsqueeze(0)

            # Inference
            with torch.no_grad():
                outputs = self._model(batch_tensor)
                probs = nn_f.softmax(outputs[0], dim=0)

            _, top_catid = torch.topk(probs, 1)
            category_name = self._categories[top_catid[0].item()].lower()

            # Map ImageNet class names to our high-level scene labels
            if any(k in category_name for k in ["screen", "monitor", "television", "projection"]):
                return "presentation slide"
            elif any(k in category_name for k in ["board", "chalkboard", "blackboard", "slate"]):
                return "whiteboard"
            elif any(k in category_name for k in ["notebook", "laptop", "keyboard", "computer"]):
                return "code editor"
            elif any(
                k in category_name
                for k in [  # noqa: E501
                    "valley",
                    "cliff",
                    "alp",
                    "volcano",
                    "shore",
                    "lake",
                    "forest",
                    "tree",
                    "mountain",
                ]
            ):
                return "outdoor"
            else:
                return "indoor"

        except Exception as exc:
            logger.error("Scene classification inference failed", error=str(exc))
            return "unknown"
