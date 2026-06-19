"""
VideoMind AI — Language Detection
====================================
Detects the spoken language of an audio file with a confidence score.
Used to select the appropriate Whisper language mode and log metadata.

SOLID — Single Responsibility:
    This function has a single responsibility: detecting the spoken
    language from an audio snippet. It does not transcribe the full file.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.core.exceptions import TranscriptionError
from app.core.logging import get_logger

logger = get_logger(__name__)

# Module-level cache for loading Whisper model exactly once (Singleton pattern variant)
_model_cache: dict[tuple[str, str], Any] = {}


def _get_whisper_model(model_size: str, device: str) -> Any:
    """
    Retrieve or load a Whisper model from the local cache.
    """
    key = (model_size, device)
    if key not in _model_cache:
        try:
            import whisper as _whisper
        except ImportError as exc:
            raise TranscriptionError("unknown", f"whisper import error: {exc}") from exc

        try:
            _model_cache[key] = _whisper.load_model(model_size, device=device)
        except Exception as exc:
            raise TranscriptionError("unknown", f"whisper model load failed: {exc}") from exc
    return _model_cache[key]


def detect_language(audio_path: str) -> tuple[str, float]:
    """
    Detect the primary spoken language of an audio file.

    Args:
        audio_path: Path to a WAV audio file.

    Returns:
        Tuple of (language_code, confidence) e.g. ("en", 0.98).

    Raises:
        TranscriptionError: If detection fails.
    """
    src = Path(audio_path)
    if not src.exists():
        raise TranscriptionError("unknown", "audio file not found")

    try:
        import whisper
    except ImportError as exc:
        raise TranscriptionError("unknown", f"whisper import error: {exc}") from exc

    try:
        settings = get_settings()
        model = _get_whisper_model(settings.whisper_model, settings.whisper_device)

        # load audio and pad/trim it to fit 30 seconds
        audio = whisper.load_audio(str(src))
        audio = whisper.pad_or_trim(audio)

        # make log-Mel spectrogram and move to the same device as the model
        mel = whisper.log_mel_spectrogram(audio).to(model.device)

        # detect the spoken language
        _, probs = model.detect_language(mel)
        detected_lang = max(probs, key=probs.get)
        confidence = probs[detected_lang]

        logger.info(
            "Whisper language detection completed",
            audio_path=audio_path,
            language=detected_lang,
            confidence=confidence,
        )
        return detected_lang, confidence

    except Exception as exc:
        logger.exception("Language detection failed", error=str(exc))
        raise TranscriptionError("unknown", f"language detection error: {exc}") from exc
