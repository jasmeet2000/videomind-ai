import os
import tempfile
import types
import unittest
from unittest.mock import patch

from app.core.exceptions import TranscriptionError
from app.speech.whisper_service import WhisperService


class TestWhisperService(unittest.TestCase):
    def test_transcribe_missing_file_raises(self):
        svc = WhisperService(model_size="tiny", device="cpu")
        with self.assertRaises(TranscriptionError):
            svc.transcribe("nonexistent_audio_12345.wav", "vid123")

    def test_transcribe_with_mock_whisper(self):
        # Create a mock whisper module
        class MockModel:
            def transcribe(self, path, language=None):
                return {
                    "segments": [
                        {"start": 0.0, "end": 1.2, "text": "Hello world.", "confidence": 0.95}
                    ],
                    "language": "en",
                }

        mock_whisper = types.ModuleType("whisper")

        def load_model(name, device=None):
            return MockModel()

        mock_whisper.load_model = load_model

        # Create a temporary empty wav file to satisfy existence check
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.close()
        try:
            with patch.dict("sys.modules", {"whisper": mock_whisper}):
                svc = WhisperService(model_size="tiny", device="cpu")
                chunks = svc.transcribe(tmp.name, "vid123")
                self.assertEqual(len(chunks), 1)
                self.assertEqual(chunks[0].text, "Hello world.")
                self.assertAlmostEqual(chunks[0].start_seconds, 0.0)
                self.assertEqual(chunks[0].language, "en")
        finally:
            os.unlink(tmp.name)


if __name__ == '__main__':
    unittest.main()
