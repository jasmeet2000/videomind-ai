"""
VideoMind AI — EasyOCR Adapter
===============================
Adapts the EasyOCR library to the IOCREngine interface.

SOLID Principle — Single Responsibility (SRP):
    Only performs EasyOCR setup and extraction. Does not handle fallback logic.

SOLID Principle — Liskov Substitution (LSP) / Dependency Inversion (DIP):
    Implements the IOCREngine interface, making it interchangeable with any
    other OCR engine adapter.
"""

from __future__ import annotations

import numpy as np

from app.core.exceptions import OCREngineUnavailableError
from app.core.logging import get_logger
from app.domain.entities import TextBlock
from app.domain.interfaces import IOCREngine

logger = get_logger(__name__)


class EasyOCRAdapter(IOCREngine):
    """
    Adapts EasyOCR for text extraction from video frames.
    """

    def __init__(self, langs: list[str] | None = None, gpu: bool = False) -> None:
        """
        Initialize the adapter configuration.
        """
        self.langs = langs or ["en"]
        self.gpu = gpu
        self._reader = None

    def _init_reader(self) -> None:
        """
        Lazily initialize the EasyOCR Reader instance.
        """
        if self._reader is None:
            try:
                import easyocr
                self._reader = easyocr.Reader(self.langs, gpu=self.gpu)
            except Exception as exc:
                logger.error("Failed to load EasyOCR", error=str(exc))
                raise OCREngineUnavailableError() from exc

    def extract(self, image: np.ndarray) -> list[TextBlock]:
        """
        Extract text blocks from a BGR image array.

        Args:
            image: BGR image array (H x W x 3) from OpenCV.

        Returns:
            List of TextBlock instances with text, confidence, and bounding box.
        """
        self._init_reader()

        try:
            # easyocr.readtext takes BGR or RGB numpy arrays
            results = self._reader.readtext(image)
        except Exception as exc:
            logger.error("EasyOCR extraction failed", error=str(exc))
            return []

        blocks: list[TextBlock] = []
        for res in results:
            try:
                coords, text, confidence = res
                pts = coords
                x = int(min(pt[0] for pt in pts))
                y = int(min(pt[1] for pt in pts))
                w = int(max(pt[0] for pt in pts) - x)
                h = int(max(pt[1] for pt in pts) - y)

                blocks.append(
                    TextBlock(
                        text=text,
                        confidence=float(confidence),
                        bounding_box=(x, y, w, h),
                    )
                )
            except Exception as parse_exc:
                logger.warning("Failed to parse EasyOCR result", error=str(parse_exc))
                continue

        return blocks

    def is_available(self) -> bool:
        """
        Return True if the easyocr library is installed and loadable.
        """
        try:
            import easyocr  # noqa: F401
            return True
        except ImportError:
            return False
