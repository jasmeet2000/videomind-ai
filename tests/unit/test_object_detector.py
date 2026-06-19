"""
Unit tests for ObjectDetector.

Strategy: Bypass lazy _init_model() by directly injecting a mock model
and categories onto the detector instance. This avoids patching sys.modules
(which would break numpy/PIL) while still validating the full detect() path.
"""

import unittest
from unittest.mock import MagicMock, patch

import numpy as np

from app.vision.object_detector import ObjectDetector


class TestObjectDetector(unittest.TestCase):

    def _make_detector(self, categories=None, confidence_threshold=0.5) -> ObjectDetector:
        """Return a fully initialised ObjectDetector with injected mocks."""
        if categories is None:
            categories = ["background", "person", "bicycle", "car", "laptop", "mouse"]
        detector = ObjectDetector(confidence_threshold=confidence_threshold)

        mock_model = MagicMock()
        pred = {
            "scores": MagicMock(tolist=lambda: [0.9, 0.4, 0.8]),
            "labels": MagicMock(tolist=lambda: [1, 2, 4]),  # person, bicycle, laptop
        }
        mock_model.return_value = [pred]
        detector._model = mock_model
        detector._categories = categories
        return detector

    def _make_torch_ctx(self):
        """Return a configured mock torch with a no_grad passthrough."""
        mock_torch = MagicMock()
        mock_torch.no_grad.return_value.__enter__ = MagicMock(return_value=None)
        mock_torch.no_grad.return_value.__exit__ = MagicMock(return_value=False)
        return mock_torch

    def _make_f_mock(self):
        """Return a configured torchvision.transforms.functional mock."""
        mock_f = MagicMock()
        mock_tensor = MagicMock()
        mock_tensor.unsqueeze.return_value = mock_tensor
        mock_f.to_tensor.return_value = mock_tensor
        return mock_f

    def test_object_detector_success(self):
        """Detects labels above confidence_threshold, filters below."""
        detector = self._make_detector(confidence_threshold=0.5)
        dummy_image = np.zeros((100, 100, 3), dtype=np.uint8)

        with patch("app.vision.object_detector.Image"), \
             patch("app.vision.object_detector.F", self._make_f_mock()), \
             patch("app.vision.object_detector.torch", self._make_torch_ctx()):
            res = detector.detect(dummy_image)

        # score 0.9 → person (idx 1), score 0.8 → laptop (idx 4); bicycle filtered
        self.assertIn("person", res)
        self.assertIn("laptop", res)
        self.assertNotIn("bicycle", res)
        self.assertEqual(len(res), 2)

    def test_object_detector_no_predictions(self):
        """Returns empty list when model returns no predictions."""
        detector = self._make_detector()
        detector._model = MagicMock(return_value=[])
        dummy_image = np.zeros((100, 100, 3), dtype=np.uint8)

        with patch("app.vision.object_detector.Image"), \
             patch("app.vision.object_detector.F", self._make_f_mock()), \
             patch("app.vision.object_detector.torch", self._make_torch_ctx()):
            res = detector.detect(dummy_image)

        self.assertEqual(res, [])

    def test_object_detector_all_below_threshold(self):
        """Returns empty list when all scores are below threshold."""
        detector = self._make_detector(confidence_threshold=0.99)
        dummy_image = np.zeros((100, 100, 3), dtype=np.uint8)

        with patch("app.vision.object_detector.Image"), \
             patch("app.vision.object_detector.F", self._make_f_mock()), \
             patch("app.vision.object_detector.torch", self._make_torch_ctx()):
            res = detector.detect(dummy_image)

        self.assertEqual(res, [])

    def test_object_detector_model_not_loaded(self):
        """Returns empty list when model failed to initialise."""
        detector = ObjectDetector()
        detector._model = False  # simulates init failure
        dummy_image = np.zeros((100, 100, 3), dtype=np.uint8)
        self.assertEqual(detector.detect(dummy_image), [])

    def test_object_detector_deduplicates_labels(self):
        """Each unique label appears only once in the result."""
        detector = self._make_detector(confidence_threshold=0.5)
        pred = {
            "scores": MagicMock(tolist=lambda: [0.9, 0.95]),
            "labels": MagicMock(tolist=lambda: [1, 1]),  # two "person" detections
        }
        detector._model.return_value = [pred]
        dummy_image = np.zeros((100, 100, 3), dtype=np.uint8)

        with patch("app.vision.object_detector.Image"), \
             patch("app.vision.object_detector.F", self._make_f_mock()), \
             patch("app.vision.object_detector.torch", self._make_torch_ctx()):
            res = detector.detect(dummy_image)

        self.assertEqual(res.count("person"), 1)


if __name__ == "__main__":
    unittest.main()
