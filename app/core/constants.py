"""
VideoMind AI — Named Constants
================================
Single source of truth for all magic numbers, thresholds, and enum-like values.

DRY Principle:
    All thresholds live here. Changing OCR_CONFIDENCE_THRESHOLD in one
    place updates every consumer — no scattered magic numbers.

KISS Principle:
    Plain module-level constants are simpler than a Config class for
    values that never come from the environment (they are code constants,
    not deployment variables).
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Supported video formats (Fail Fast — validated at upload)
# ---------------------------------------------------------------------------
SUPPORTED_VIDEO_EXTENSIONS: frozenset[str] = frozenset({
    ".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".m4v",
})

SUPPORTED_AUDIO_EXTENSIONS: frozenset[str] = frozenset({
    ".mp3", ".wav", ".flac", ".ogg", ".m4a",
})

# ---------------------------------------------------------------------------
# Video processing
# ---------------------------------------------------------------------------
MIN_VIDEO_DURATION_SECONDS: float = 1.0
MAX_VIDEO_DURATION_SECONDS: float = 7200.0    # 2 hours max
DEFAULT_FRAME_SAMPLE_RATE_FPS: float = 1.0    # 1 frame per second
FRAME_IMAGE_FORMAT: str = "jpg"
FRAME_JPEG_QUALITY: int = 85                  # JPEG quality [0-100]
AUDIO_SAMPLE_RATE_HZ: int = 16_000            # Whisper requires 16 kHz

# ---------------------------------------------------------------------------
# Speech / Transcription
# ---------------------------------------------------------------------------
WHISPER_MODEL_SIZES: tuple[str, ...] = ("tiny", "base", "small", "medium", "large")
TRANSCRIPT_CHUNK_MAX_TOKENS: int = 512        # Max tokens per indexed chunk
TRANSCRIPT_OVERLAP_TOKENS: int = 50          # Overlap between adjacent chunks

# ---------------------------------------------------------------------------
# OCR
# ---------------------------------------------------------------------------
OCR_CONFIDENCE_THRESHOLD: float = 0.7        # Below this → try fallback engine
OCR_MIN_TEXT_LENGTH: int = 3                 # Ignore single/double char noise

# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------
EMBEDDING_DIMENSION_BGE_SMALL: int = 384     # BAAI/bge-small-en-v1.5
EMBEDDING_DIMENSION_NOMIC: int = 768         # nomic-embed-text

# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------
DENSE_TOP_K_DEFAULT: int = 10
RERANK_TOP_K_DEFAULT: int = 5
HYBRID_ALPHA_DEFAULT: float = 0.7            # 70% dense, 30% sparse
BM25_K1: float = 1.5                         # BM25 term saturation parameter
BM25_B: float = 0.75                         # BM25 length normalization

# ---------------------------------------------------------------------------
# Qdrant collection names
# ---------------------------------------------------------------------------
QDRANT_TRANSCRIPT_COLLECTION: str = "transcript_chunks"
QDRANT_FRAME_COLLECTION: str = "frame_descriptions"

# ---------------------------------------------------------------------------
# LLM generation
# ---------------------------------------------------------------------------
LLM_MAX_CONTEXT_CHUNKS: int = 8              # Max chunks included in RAG context
LLM_MAX_RESPONSE_TOKENS: int = 1024
LLM_TEMPERATURE: float = 0.1                 # Low temperature → factual answers

# ---------------------------------------------------------------------------
# Pipeline stage names (used in PipelineEvent.stage)
# ---------------------------------------------------------------------------
STAGE_METADATA_EXTRACTION: str = "metadata_extraction"
STAGE_AUDIO_EXTRACTION: str = "audio_extraction"
STAGE_FRAME_EXTRACTION: str = "frame_extraction"
STAGE_TRANSCRIPTION: str = "transcription"
STAGE_OCR: str = "ocr"
STAGE_OBJECT_DETECTION: str = "object_detection"
STAGE_EMBEDDING: str = "embedding"
STAGE_VECTOR_UPSERT: str = "vector_upsert"
STAGE_RETRIEVAL: str = "retrieval"
STAGE_RERANKING: str = "reranking"
STAGE_GENERATION: str = "generation"
