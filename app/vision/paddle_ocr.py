"""
VideoMind AI — PaddleOCR Adapter
=================================
Adapts the PaddleOCR library to the IOCREngine interface.

SOLID Principle — Single Responsibility (SRP):
    Only performs PaddleOCR setup and extraction. Does not handle fallback logic.

SOLID Principle — Liskov Substitution (LSP) / Dependency Inversion (DIP):
    Implements the IOCREngine interface, making it interchangeable with any
    other OCR engine adapter.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.exceptions import OCREngineUnavailableError
from app.core.logging import get_logger
from app.domain.entities import TextBlock
from app.domain.interfaces import IOCREngine

if TYPE_CHECKING:
    import numpy as np

logger = get_logger(__name__)


class PaddleOCRAdapter(IOCREngine):
    """
    Adapts PaddleOCR for text extraction from video frames.
    """

    def __init__(self, lang: str = "en", use_gpu: bool = False) -> None:
        """
        Initialize the adapter configuration.
        """
        self.lang = lang
        self.use_gpu = use_gpu
        self._ocr = None

    def _init_ocr(self) -> None:
        """
        Lazily initialize the PaddleOCR reader instance.
        """
        if self._ocr is None:
            try:
                from paddleocr import PaddleOCR

                # PaddleOCR generates verbose logs; show_log=False keeps it quiet
                self._ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang=self.lang,
                    use_gpu=self.use_gpu,
                    show_log=False,
                )
            except Exception as exc:
                logger.error("Failed to load PaddleOCR", error=str(exc))
                raise OCREngineUnavailableError() from exc

    def extract(self, image: np.ndarray) -> list[TextBlock]:
        """
        Extract text blocks from a BGR image array.

        Args:
            image: BGR image array (H x W x 3) from OpenCV.

        Returns:
            List of TextBlock instances with text, confidence, and bounding box.
        """
        self._init_ocr()

        try:
            # self._ocr.ocr returns a list of results (one per page/frame)
            results = self._ocr.ocr(image, cls=True)
        except Exception as exc:
            logger.error("PaddleOCR extraction failed", error=str(exc))
            return []

        blocks: list[TextBlock] = []
        if not results:
            return blocks

        for line in results:
            if not line:
                continue
            for res in line:
                try:
                    coords, (text, confidence) = res
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
                    logger.warning("Failed to parse PaddleOCR result line", error=str(parse_exc))
                    continue

        return blocks

    def is_available(self) -> bool:
        """
        Return True if the paddleocr library is installed and loadable.
        """
        try:
            import paddleocr  # noqa: F401

            return True
        except ImportError:
            return False
