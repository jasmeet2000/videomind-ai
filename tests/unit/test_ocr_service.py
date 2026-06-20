import unittest
from unittest.mock import MagicMock, patch

import numpy as np

from app.domain.entities import TextBlock
from app.vision.easy_ocr import EasyOCRAdapter
from app.vision.ocr_service import OCRService, get_ocr_service
from app.vision.paddle_ocr import PaddleOCRAdapter


class FakeEngine:
    def __init__(self, blocks):
        self._blocks = blocks

    def extract(self, image):
        return self._blocks

    def is_available(self):
        return True


def make_block(text, conf):
    return TextBlock(text=text, confidence=conf, bounding_box=(0, 0, 10, 10))


class TestOCRService(unittest.TestCase):
    def test_no_fallback_returns_primary(self):
        primary = FakeEngine([make_block("hi", 0.9)])
        svc = OCRService(primary, None, confidence_threshold=0.8)
        res = svc.extract(np.zeros((10, 10, 3), dtype=np.uint8))
        self.assertEqual(res, primary._blocks)

    def test_fallback_on_low_conf(self):
        primary = FakeEngine([make_block("hi", 0.5)])
        fallback = FakeEngine([make_block("fallback", 0.95)])
        svc = OCRService(primary, fallback, confidence_threshold=0.8)
        res = svc.extract(np.zeros((10, 10, 3), dtype=np.uint8))
        self.assertEqual(res, fallback._blocks)

    def test_fallback_failure_keeps_primary(self):
        class BrokenEngine:
            def extract(self, image):
                raise RuntimeError("boom")

        primary = FakeEngine([make_block("hi", 0.5)])
        broken = BrokenEngine()
        svc = OCRService(primary, broken, confidence_threshold=0.8)
        res = svc.extract(np.zeros((10, 10, 3), dtype=np.uint8))
        self.assertEqual(res, primary._blocks)

    @patch("sys.modules", {"paddleocr": MagicMock()})
    def test_paddle_ocr_adapter_success(self):
        import paddleocr

        mock_instance = MagicMock()
        mock_instance.ocr.return_value = [[[[[0, 0], [10, 0], [10, 10], [0, 10]], ("hello", 0.9)]]]
        paddleocr.PaddleOCR.return_value = mock_instance

        adapter = PaddleOCRAdapter()
        res = adapter.extract(np.zeros((100, 100, 3), dtype=np.uint8))
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].text, "hello")
        self.assertAlmostEqual(res[0].confidence, 0.9)
        self.assertEqual(res[0].bounding_box, (0, 0, 10, 10))
        self.assertTrue(adapter.is_available())

    @patch("sys.modules", {"easyocr": MagicMock()})
    def test_easy_ocr_adapter_success(self):
        import easyocr

        mock_instance = MagicMock()
        mock_instance.readtext.return_value = [
            ([[0, 0], [10, 0], [10, 10], [0, 10]], "world", 0.85)
        ]
        easyocr.Reader.return_value = mock_instance

        adapter = EasyOCRAdapter()
        res = adapter.extract(np.zeros((100, 100, 3), dtype=np.uint8))
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].text, "world")
        self.assertAlmostEqual(res[0].confidence, 0.85)
        self.assertEqual(res[0].bounding_box, (0, 0, 10, 10))
        self.assertTrue(adapter.is_available())

    @patch("app.core.config.get_settings")
    def test_get_ocr_service_paddle(self, mock_settings):
        mock_set = MagicMock()
        mock_set.ocr_engine = "paddleocr"
        mock_set.ocr_confidence_threshold = 0.75
        mock_settings.return_value = mock_set

        svc = get_ocr_service()
        self.assertIsNotNone(svc.engine)
        self.assertIsNotNone(svc.fallback_engine)
        self.assertEqual(svc.confidence_threshold, 0.75)


if __name__ == "__main__":
    unittest.main()
