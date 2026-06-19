"""
VideoMind AI — Language Detection
====================================
Detects the spoken language of an audio file with a confidence score.
Used to select the appropriate Whisper language mode and log metadata.

SOLID — Single Responsibility:
    Only detects language. Transcription is handled by WhisperService.
"""

from __future__ import annotations

# Stub — implementation in Phase 4


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
    raise NotImplementedError("Phase 4: Implement language detection via Whisper")
