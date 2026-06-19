"""
VideoMind AI — Whisper Transcription Service
==============================================
Wraps the OpenAI Whisper model to produce timestamped transcript chunks.

SOLID — Single Responsibility:
    Only transcribes audio. Does not chunk, embed, or save results.

SOLID — Dependency Inversion:
    Depends on the IEmbeddingModel interface via the Settings injected
    at construction time, not on a concrete model class.

DESIGN PATTERN — Strategy:
    WhisperService accepts a model size at construction — swapping from
    "base" to "medium" or distil-whisper requires no caller changes.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from app.core.config import get_settings
from app.core.exceptions import TranscriptionError
from app.core.logging import get_logger
from app.domain.entities import TranscriptChunk

settings = get_settings()
logger = get_logger(__name__)


class WhisperService:
    """
    Transcribes audio files using OpenAI Whisper with timestamped segments.

    This implementation loads the Whisper model lazily. In CI and unit
    tests the whisper module may be mocked; code defers importing it until
    a transcription is requested to avoid import-time failures.
    """

    def __init__(self, model_size: str = "base", device: str = "cpu") -> None:
        """
        Args:
            model_size: Whisper model variant ("tiny", "base", "small", etc.).
            device: PyTorch device string ("cpu" or "cuda").
        """
        self.model_size = model_size
        self.device = device
        self._model = None  # Lazy-loaded on first call (expensive)
        self.language = get_settings().whisper_language
        self._whisper_module = None

    def transcribe(self, audio_path: str, video_id: str) -> List[TranscriptChunk]:
        """
        Transcribe an audio file and return timestamped chunks.

        Args:
            audio_path: Path to a 16 kHz mono WAV file.
            video_id: Parent video ID to embed in each TranscriptChunk.

        Returns:
            List of TranscriptChunk with text, start_seconds, end_seconds,
            confidence, and detected language.

        Raises:
            TranscriptionError: If the Whisper model fails.
        """
        src = Path(audio_path)
        if not src.exists():
            raise TranscriptionError(video_id, "audio file not found")

        # Lazy-load whisper model
        if self._model is None:
            try:
                import whisper as _whisper
            except Exception as exc:  # pragma: no cover - import-time failures
                logger.exception("whisper import failed", error=str(exc))
                raise TranscriptionError(video_id, f"whisper import error: {exc}")

            try:
                self._model = _whisper.load_model(self.model_size, device=self.device)
                self._whisper_module = _whisper
            except Exception as exc:  # pragma: no cover - model load failures
                logger.exception("whisper model load failed", error=str(exc))
                raise TranscriptionError(video_id, f"whisper load error: {exc}")

        # Run transcription
        try:
            result = self._model.transcribe(str(src), language=self.language)
        except Exception as exc:  # pragma: no cover - runtime transcription errors
            logger.exception("Whisper transcription failed", error=str(exc))
            raise TranscriptionError(video_id, f"whisper transcription error: {exc}")

        # Normalize result -> list of segments
        if isinstance(result, dict):
            segments = result.get("segments", []) or []
            detected_language = result.get("language", self.language)
        else:
            segments = getattr(result, "segments", []) or []
            detected_language = getattr(result, "language", self.language)

        chunks: List[TranscriptChunk] = []
        for seg in segments:
            if isinstance(seg, dict):
                text = seg.get("text", "").strip()
                start = float(seg.get("start", 0.0))
                end = float(seg.get("end", 0.0))
                # confidence mapping is model-specific; prefer explicit keys
                confidence = 0.0
                if "confidence" in seg:
                    try:
                        confidence = float(seg.get("confidence") or 0.0)
                    except Exception:
                        confidence = 0.0
            else:
                text = getattr(seg, "text", "").strip()
                start = float(getattr(seg, "start", 0.0))
                end = float(getattr(seg, "end", 0.0))
                confidence = float(getattr(seg, "confidence", 0.0)) if getattr(seg, "confidence", None) is not None else 0.0

            chunk = TranscriptChunk(
                video_id=video_id,
                text=text,
                start_seconds=start,
                end_seconds=end,
                confidence=confidence,
                language=detected_language or self.language,
            )
            chunks.append(chunk)

        # Chunk the transcript into indexable chunks using the chunker
        try:
            from app.core.constants import TRANSCRIPT_CHUNK_MAX_TOKENS, TRANSCRIPT_OVERLAP_TOKENS
            from app.speech.chunker import chunk_transcript_chunks
            return chunk_transcript_chunks(
                chunks,
                max_tokens=TRANSCRIPT_CHUNK_MAX_TOKENS,
                overlap_tokens=TRANSCRIPT_OVERLAP_TOKENS,
            )
        except Exception as exc:  # pragma: no cover - non-critical
            logger.exception("chunking failed", error=str(exc))
            return chunks
