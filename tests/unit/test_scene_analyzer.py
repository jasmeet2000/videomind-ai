"""
Unit tests for SceneAnalyzer.

Strategy: Bypass lazy _init_model() by directly injecting a mock model and
categories onto the analyzer instance. Module-level names (torch, nn_f,
Image, F) are patched so no real torchvision weights are loaded.
"""

import unittest
from unittest.mock import MagicMock, patch

import numpy as np

from app.vision.scene_analyzer import SceneAnalyzer

# Canonical category list aligned with the domain-mapping keywords in classify()
_CATEGORIES = [
    "background",     # 0
    "screen",         # 1  → "presentation slide"
    "blackboard",     # 2  → "whiteboard"
    "notebook",       # 3  → "code editor"
    "lake",           # 4  → "outdoor"
    "dog",            # 5  → "indoor" (default)
]


def _make_analyzer(categories=None) -> SceneAnalyzer:
    """Return a SceneAnalyzer with mocks pre-injected (skips _init_model)."""
    analyzer = SceneAnalyzer()
    analyzer._categories = categories or _CATEGORIES
    mock_model = MagicMock()
    mock_model.return_value = MagicMock()
    analyzer._model = mock_model
    return analyzer


def _run_classify(analyzer: SceneAnalyzer, top_index: int) -> str:
    """
    Run analyzer.classify() with module-level mocks patched so that
    torch.topk returns top_index as the winner.
    """
    dummy_image = np.zeros((100, 100, 3), dtype=np.uint8)

    mock_topk_index = MagicMock()
    mock_topk_index.item.return_value = top_index

    mock_tensor = MagicMock()
    mock_tensor.unsqueeze.return_value = mock_tensor

    mock_f = MagicMock()
    mock_f.resize.return_value = MagicMock()
    mock_f.to_tensor.return_value = MagicMock()
    mock_f.normalize.return_value = mock_tensor

    mock_torch = MagicMock()
    mock_torch.no_grad.return_value.__enter__ = MagicMock(return_value=None)
    mock_torch.no_grad.return_value.__exit__ = MagicMock(return_value=False)
    mock_torch.topk.return_value = (MagicMock(), [mock_topk_index])

    mock_nn_f = MagicMock()
    mock_nn_f.softmax.return_value = MagicMock()

    with patch("app.vision.scene_analyzer.Image") as mock_pil, \
         patch("app.vision.scene_analyzer.F", mock_f), \
         patch("app.vision.scene_analyzer.torch", mock_torch), \
         patch("app.vision.scene_analyzer.nn_f", mock_nn_f):
        mock_pil.fromarray.return_value = MagicMock()
        return analyzer.classify(dummy_image)


class TestSceneAnalyzer(unittest.TestCase):

    def test_scene_analyzer_presentation_slide(self):
        """Category 'screen' maps to 'presentation slide'."""
        self.assertEqual(_run_classify(_make_analyzer(), 1), "presentation slide")

    def test_scene_analyzer_whiteboard(self):
        """Category 'blackboard' maps to 'whiteboard'."""
        self.assertEqual(_run_classify(_make_analyzer(), 2), "whiteboard")

    def test_scene_analyzer_code_editor(self):
        """Category 'notebook' maps to 'code editor'."""
        self.assertEqual(_run_classify(_make_analyzer(), 3), "code editor")

    def test_scene_analyzer_outdoor(self):
        """Category 'lake' maps to 'outdoor'."""
        self.assertEqual(_run_classify(_make_analyzer(), 4), "outdoor")

    def test_scene_analyzer_indoor_default(self):
        """Category 'dog' (no keyword match) defaults to 'indoor'."""
        self.assertEqual(_run_classify(_make_analyzer(), 5), "indoor")

    def test_scene_analyzer_model_not_loaded(self):
        """Returns 'unknown' when _model failed to initialise."""
        analyzer = SceneAnalyzer()
        analyzer._model = False
        dummy_image = np.zeros((100, 100, 3), dtype=np.uint8)
        self.assertEqual(analyzer.classify(dummy_image), "unknown")

    def test_scene_analyzer_no_categories(self):
        """Returns 'unknown' when categories list is None."""
        analyzer = SceneAnalyzer()
        analyzer._model = MagicMock()
        analyzer._categories = None
        dummy_image = np.zeros((100, 100, 3), dtype=np.uint8)
        self.assertEqual(analyzer.classify(dummy_image), "unknown")


if __name__ == "__main__":
    unittest.main()
