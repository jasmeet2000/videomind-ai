import unittest

from app.core import constants


class TestCoreConstants(unittest.TestCase):
    def test_supported_video_extensions(self):
        self.assertIn('.mp4', constants.SUPPORTED_VIDEO_EXTENSIONS)

    def test_embedding_dimensions_positive(self):
        self.assertGreater(constants.EMBEDDING_DIMENSION_BGE_SMALL, 0)

    def test_ocr_threshold_range(self):
        self.assertGreaterEqual(constants.OCR_CONFIDENCE_THRESHOLD, 0.0)
        self.assertLessEqual(constants.OCR_CONFIDENCE_THRESHOLD, 1.0)


if __name__ == '__main__':
    unittest.main()
