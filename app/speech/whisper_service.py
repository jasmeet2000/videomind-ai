"""
VideoMind AI — Whisper Transcription Service
==============================================
Wraps the Whisper model to produce timestamped transcript chunks.

SOLID — Single Responsibility:
    Only transcribes audio. Does not chunk, embed, or save results.

SOLID — Dependency Inversion:
    Depends on the IEmbeddingModel interface via the Settings injected
    at construction time, not on a concrete model class.

DESIGN PATTERN — Strategy:
    WhisperService accepts a model size at construction — swapping from
    "base" to "medium" or distil-whisper requires no caller changes.

PERFORMANCE — faster-whisper preferred:
    Uses faster-whisper (CTranslate2 backend) by default, which is
    4× faster on CPU and uses ~50% less RAM than openai-whisper.
    Falls back to openai-whisper automatically if faster-whisper is
    not installed.
"""

from __future__ import annotations

from pathlib import Path

from app.core.config import get_settings
from app.core.exceptions import TranscriptionError
from app.core.logging import get_logger
from app.domain.entities import TranscriptChunk

settings = get_settings()
logger = get_logger(__name__)


class WhisperService:
    """
    Transcribes audio files using Whisper with timestamped segments.

    PERFORMANCE: Prefers faster-whisper (CTranslate2) for 4× speedup on CPU.
    Falls back to openai-whisper if faster-whisper is not installed.

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
        self._use_faster_whisper = None  # Auto-detected on first call
        self._whisper_module = None

    def _load_model(self, video_id: str) -> None:
        """Lazily load the best available Whisper implementation."""
        if self._model is not None:
            return

        # Try faster-whisper first (CTranslate2 — 4× faster on CPU, 50% less RAM)
        try:
            from faster_whisper import WhisperModel as FasterWhisperModel

            compute_type = "int8" if self.device == "cpu" else "float16"
            self._model = FasterWhisperModel(
                self.model_size,
                device=self.device,
                compute_type=compute_type,
            )
            self._use_faster_whisper = True
            logger.info(
                "Loaded faster-whisper model",
                model=self.model_size,
                device=self.device,
                compute_type=compute_type,
            )
            return
        except ImportError:
            logger.info("faster-whisper not installed, trying openai-whisper fallback")
        except Exception as exc:
            logger.warning("faster-whisper load failed, trying fallback", error=str(exc))

        # Fallback to openai-whisper
        try:
            import whisper as _whisper

            self._model = _whisper.load_model(self.model_size, device=self.device)
            self._whisper_module = _whisper
            self._use_faster_whisper = False
            logger.info(
                "Loaded openai-whisper model",
                model=self.model_size,
                device=self.device,
            )
        except Exception as exc:
            logger.exception("All whisper backends failed", error=str(exc))
            raise TranscriptionError(video_id, f"whisper load error: {exc}")

    def transcribe(self, audio_path: str, video_id: str) -> list[TranscriptChunk]:
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
        self._load_model(video_id)

        # Run transcription with the appropriate backend
        if self._use_faster_whisper:
            chunks = self._transcribe_faster_whisper(str(src), video_id)
        else:
            chunks = self._transcribe_openai_whisper(str(src), video_id)

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

    def _transcribe_faster_whisper(
        self, audio_path: str, video_id: str
    ) -> list[TranscriptChunk]:
        """Transcribe using faster-whisper (CTranslate2 backend)."""
        try:
            lang = None if self.language == "auto" else self.language
            segments, info = self._model.transcribe(audio_path, language=lang)
            detected_language = info.language or self.language

            chunks: list[TranscriptChunk] = []
            for seg in segments:
                chunk = TranscriptChunk(
                    video_id=video_id,
                    text=seg.text.strip(),
                    start_seconds=seg.start,
                    end_seconds=seg.end,
                    confidence=seg.avg_log_prob if hasattr(seg, "avg_log_prob") else 0.0,
                    language=detected_language,
                )
                chunks.append(chunk)
            return chunks
        except Exception as exc:
            logger.exception("faster-whisper transcription failed", error=str(exc))
            raise TranscriptionError(video_id, f"faster-whisper error: {exc}")

    def _transcribe_openai_whisper(
        self, audio_path: str, video_id: str
    ) -> list[TranscriptChunk]:
        """Transcribe using openai-whisper (fallback)."""
        try:
            result = self._model.transcribe(audio_path, language=self.language)
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

        chunks: list[TranscriptChunk] = []
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
                confidence = (
                    float(getattr(seg, "confidence", 0.0))
                    if getattr(seg, "confidence", None) is not None
                    else 0.0
                )

            chunk = TranscriptChunk(
                video_id=video_id,
                text=text,
                start_seconds=start,
                end_seconds=end,
                confidence=confidence,
                language=detected_language or self.language,
            )
            chunks.append(chunk)

        return chunks

