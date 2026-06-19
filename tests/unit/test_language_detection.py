import os
import tempfile
import types
import unittest
from unittest.mock import MagicMock, patch

from app.core.exceptions import TranscriptionError
from app.speech.language_detection import detect_language


class TestLanguageDetection(unittest.TestCase):
    def test_detect_language_missing_file_raises(self):
        with self.assertRaises(TranscriptionError):
            detect_language("nonexistent_audio_12345.wav")

    def test_detect_language_with_mock_whisper(self):
        # Create a mock whisper module
        class MockModel:
            def __init__(self):
                self.device = "cpu"

            def detect_language(self, mel):
                return None, {"en": 0.95, "fr": 0.05}

        mock_whisper = types.ModuleType("whisper")

        def load_model(name, device=None):
            return MockModel()

        def load_audio(path):
            return MagicMock()

        def pad_or_trim(audio):
            return audio

        def log_mel_spectrogram(audio):
            mock_mel = MagicMock()
            mock_mel.to.return_value = mock_mel
            return mock_mel

        mock_whisper.load_model = load_model
        mock_whisper.load_audio = load_audio
        mock_whisper.pad_or_trim = pad_or_trim
        mock_whisper.log_mel_spectrogram = log_mel_spectrogram

        # Create a temporary empty wav file to satisfy existence check
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_name = tmp.name
        try:
            with patch.dict("sys.modules", {"whisper": mock_whisper}), \
                 patch("app.speech.language_detection._model_cache", {}):
                lang, conf = detect_language(tmp_name)
                self.assertEqual(lang, "en")
                self.assertAlmostEqual(conf, 0.95)
        finally:
            os.unlink(tmp_name)


if __name__ == '__main__':
    unittest.main()
