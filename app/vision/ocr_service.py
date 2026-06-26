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

PERFORMANCE — Lazy Fallback Loading:
    The fallback OCR engine is wrapped in _LazyOCREngine so it is only
    loaded on first use. This avoids loading ~500MB of EasyOCR model weights
    at startup if PaddleOCR confidence is always above threshold.
"""

from __future__ import annotations

import numpy as np

from app.domain.entities import TextBlock
from app.domain.interfaces import IOCREngine

# Stub — implementation in Phase 5


class _LazyOCREngine(IOCREngine):
    """Proxy that defers OCR engine initialization until the first extract() call.

    PERFORMANCE: Loading an OCR engine (especially EasyOCR) takes 2-5 seconds
    and consumes ~500MB of RAM. This proxy ensures that cost is only paid when
    the fallback is actually needed — which may never happen if the primary
    engine's confidence stays above the threshold.
    """

    def __init__(self, factory_fn) -> None:
        self._factory_fn = factory_fn
        self._engine: IOCREngine | None = None

    def _ensure_engine(self) -> IOCREngine:
        if self._engine is None:
            self._engine = self._factory_fn()
        return self._engine

    def extract(self, image: np.ndarray) -> list[TextBlock]:
        return self._ensure_engine().extract(image)


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


# ---------------------------------------------------------------------------
# Singleton OCR service instance — loaded once and reused.
# ---------------------------------------------------------------------------
_ocr_service_instance: OCRService | None = None


def get_ocr_service() -> OCRService:
    """
    Dependency Injection / Strategy Factory:
    Loads OCR engines based on application settings.

    PERFORMANCE: Returns a cached singleton to avoid re-initializing
    OCR models on every call. The fallback engine is wrapped in
    _LazyOCREngine so it is only loaded on first use.
    """
    global _ocr_service_instance
    if _ocr_service_instance is not None:
        return _ocr_service_instance

    from app.core.config import get_settings
    from app.core.logging import get_logger
    from app.vision.paddle_ocr import PaddleOCRAdapter

    settings = get_settings()
    logger = get_logger(__name__)

    # Strategy selector registry — import adapters lazily
    engines = {
        "paddleocr": PaddleOCRAdapter,
        "easyocr": lambda: __import__(
            "app.vision.easy_ocr", fromlist=["EasyOCRAdapter"]
        ).EasyOCRAdapter,
    }

    primary_name = settings.ocr_engine.lower()
    primary_cls = engines.get(primary_name)
    if not primary_cls:
        logger.warning(
            "Configured OCR engine not found, falling back to PaddleOCR",
            engine=primary_name,
        )
        primary_cls = PaddleOCRAdapter

    primary_engine = primary_cls() if primary_name != "easyocr" else primary_cls()()

    # Configure EasyOCR as a LAZY fallback if the primary engine is PaddleOCR.
    # _LazyOCREngine ensures EasyOCR model weights (~500MB) are only loaded
    # when the primary engine's confidence is below threshold.
    fallback_engine = None
    if primary_name == "paddleocr":
        from app.vision.easy_ocr import EasyOCRAdapter
        fallback_engine = _LazyOCREngine(factory_fn=EasyOCRAdapter)

    _ocr_service_instance = OCRService(
        engine=primary_engine,
        fallback_engine=fallback_engine,
        confidence_threshold=settings.ocr_confidence_threshold,
    )
    return _ocr_service_instance

