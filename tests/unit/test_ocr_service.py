import unittest

import numpy as np

from app.domain.entities import TextBlock
from app.vision.ocr_service import OCRService


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


if __name__ == '__main__':
    unittest.main()
