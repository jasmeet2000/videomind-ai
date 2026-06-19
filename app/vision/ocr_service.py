"""
VideoMind AI — OCR Service (Strategy + Adapter)
================================================
Selects and executes the appropriate OCR engine at runtime.

DESIGN PATTERN — Strategy:
    OCRService holds a reference to the active IOCREngine. Callers call
    `ocr_service.extract(image)` without knowing which engine ran.

DESIGN PATTERN — Adapter:
    PaddleOCRAdapter and EasyOCRAdapter (defined below) wrap the external
    libraries' APIs into the uniform IOCREngine interface.

SOLID — Open/Closed:
    Adding a new OCR engine requires only a new Adapter class + registration
    in the factory dict. OCRService itself never changes.

SOLID — Liskov Substitution:
    All engines implement extract(image) -> List[TextBlock]. Swapping is safe.
"""

from __future__ import annotations

import numpy as np

from app.domain.entities import TextBlock
from app.domain.interfaces import IOCREngine

# Stub — implementation in Phase 5


class OCRService:
    """
    Selects an OCR engine based on config and delegates extraction.
    Falls back to EasyOCR if PaddleOCR confidence is below threshold.
    """

    def __init__(
        self,
        engine: IOCREngine,
        fallback_engine: IOCREngine | None = None,
        confidence_threshold: float = 0.7,
    ) -> None:
        """
        Args:
            engine: The primary IOCREngine implementation to use.
            fallback_engine: Optional IOCREngine to try when primary confidence is low.
            confidence_threshold: Below this, fallback engine is tried.
        """
        self.engine = engine
        self.fallback_engine = fallback_engine
        self.confidence_threshold = confidence_threshold

    def extract(self, image: np.ndarray) -> list[TextBlock]:
        """
        Extract text blocks from an image using the configured engine.

        If the primary engine's average confidence is below the configured
        threshold and a fallback engine is provided, the fallback engine is
        attempted and its results are returned if available.
        """
        primary_blocks = self.engine.extract(image)

        # If no fallback configured, return primary result
        if not self.fallback_engine:
            return primary_blocks

        # If primary produced nothing, return it (nothing to do)
        if not primary_blocks:
            return primary_blocks

        avg_conf = sum((b.confidence or 0.0) for b in primary_blocks) / len(primary_blocks)
        if avg_conf >= self.confidence_threshold:
            return primary_blocks

        # Try fallback engine; if it fails or returns nothing, keep primary
        try:
            fallback_blocks = self.fallback_engine.extract(image)
            if fallback_blocks:
                return fallback_blocks
            return primary_blocks
        except Exception:
            return primary_blocks


def get_ocr_service() -> OCRService:
    """
    Dependency Injection / Strategy Factory:
    Loads OCR engines based on application settings.
    """
    from app.core.config import get_settings
    from app.core.logging import get_logger
    from app.vision.easy_ocr import EasyOCRAdapter
    from app.vision.paddle_ocr import PaddleOCRAdapter

    settings = get_settings()
    logger = get_logger(__name__)

    # Strategy selector registry
    engines = {
        "paddleocr": PaddleOCRAdapter,
        "easyocr": EasyOCRAdapter,
    }

    primary_name = settings.ocr_engine.lower()
    primary_cls = engines.get(primary_name)
    if not primary_cls:
        logger.warning(
            "Configured OCR engine not found, falling back to PaddleOCR",
            engine=primary_name,
        )
        primary_cls = PaddleOCRAdapter

    primary_engine = primary_cls()

    # Configure EasyOCR as fallback if the primary engine is PaddleOCR
    fallback_engine = None
    if primary_name == "paddleocr":
        fallback_engine = EasyOCRAdapter()

    return OCRService(
        engine=primary_engine,
        fallback_engine=fallback_engine,
        confidence_threshold=settings.ocr_confidence_threshold,
    )
