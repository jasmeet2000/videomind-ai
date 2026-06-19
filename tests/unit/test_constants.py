"""
Unit tests for app/core/constants.py

Tests verify:
- All collections/sets are non-empty
- Numeric thresholds are in valid ranges
- Stage name strings are non-empty
- No magic numbers — constants are used, not re-stated

DRY Principle validation:
    If a magic number appears in two places (test + constants), that's
    acceptable — tests validate the contract, not the implementation.
"""

from __future__ import annotations

from app.core.constants import (
    AUDIO_SAMPLE_RATE_HZ,
    BM25_B,
    BM25_K1,
    DEFAULT_FRAME_SAMPLE_RATE_FPS,
    DENSE_TOP_K_DEFAULT,
    EMBEDDING_DIMENSION_BGE_SMALL,
    EMBEDDING_DIMENSION_NOMIC,
    FRAME_JPEG_QUALITY,
    HYBRID_ALPHA_DEFAULT,
    LLM_MAX_CONTEXT_CHUNKS,
    LLM_MAX_RESPONSE_TOKENS,
    LLM_TEMPERATURE,
    MAX_VIDEO_DURATION_SECONDS,
    MIN_VIDEO_DURATION_SECONDS,
    OCR_CONFIDENCE_THRESHOLD,
    OCR_MIN_TEXT_LENGTH,
    QDRANT_FRAME_COLLECTION,
    QDRANT_TRANSCRIPT_COLLECTION,
    RERANK_TOP_K_DEFAULT,
    STAGE_AUDIO_EXTRACTION,
    STAGE_EMBEDDING,
    STAGE_FRAME_EXTRACTION,
    STAGE_GENERATION,
    STAGE_METADATA_EXTRACTION,
    STAGE_OBJECT_DETECTION,
    STAGE_OCR,
    STAGE_RERANKING,
    STAGE_RETRIEVAL,
    STAGE_TRANSCRIPTION,
    STAGE_VECTOR_UPSERT,
    SUPPORTED_AUDIO_EXTENSIONS,
    SUPPORTED_VIDEO_EXTENSIONS,
    TRANSCRIPT_CHUNK_MAX_TOKENS,
    TRANSCRIPT_OVERLAP_TOKENS,
    WHISPER_MODEL_SIZES,
)


class TestVideoFormats:
    def test_supported_video_extensions_non_empty(self) -> None:
        assert len(SUPPORTED_VIDEO_EXTENSIONS) > 0

    def test_mp4_is_supported(self) -> None:
        assert ".mp4" in SUPPORTED_VIDEO_EXTENSIONS

    def test_mkv_is_supported(self) -> None:
        assert ".mkv" in SUPPORTED_VIDEO_EXTENSIONS

    def test_extensions_start_with_dot(self) -> None:
        for ext in SUPPORTED_VIDEO_EXTENSIONS:
            assert ext.startswith("."), f"Extension {ext!r} must start with '.'"

    def test_audio_extensions_non_empty(self) -> None:
        assert len(SUPPORTED_AUDIO_EXTENSIONS) > 0

    def test_wav_is_supported_audio(self) -> None:
        assert ".wav" in SUPPORTED_AUDIO_EXTENSIONS

    def test_extensions_are_lowercase(self) -> None:
        for ext in SUPPORTED_VIDEO_EXTENSIONS | SUPPORTED_AUDIO_EXTENSIONS:
            assert ext == ext.lower(), f"{ext!r} must be lowercase"


class TestVideoDuration:
    def test_min_duration_positive(self) -> None:
        assert MIN_VIDEO_DURATION_SECONDS > 0

    def test_max_duration_greater_than_min(self) -> None:
        assert MAX_VIDEO_DURATION_SECONDS > MIN_VIDEO_DURATION_SECONDS

    def test_max_duration_reasonable(self) -> None:
        # 2 hours max seems reasonable — assert it's at least 30 minutes
        assert MAX_VIDEO_DURATION_SECONDS >= 1800


class TestFrameProcessing:
    def test_frame_sample_rate_positive(self) -> None:
        assert DEFAULT_FRAME_SAMPLE_RATE_FPS > 0

    def test_jpeg_quality_in_range(self) -> None:
        assert 0 <= FRAME_JPEG_QUALITY <= 100

    def test_audio_sample_rate_for_whisper(self) -> None:
        # Whisper requires exactly 16 kHz
        assert AUDIO_SAMPLE_RATE_HZ == 16_000


class TestOCR:
    def test_confidence_threshold_in_range(self) -> None:
        assert 0.0 <= OCR_CONFIDENCE_THRESHOLD <= 1.0

    def test_min_text_length_positive(self) -> None:
        assert OCR_MIN_TEXT_LENGTH > 0


class TestEmbeddings:
    def test_bge_small_dimension_correct(self) -> None:
        """BAAI/bge-small-en-v1.5 outputs 384-dimensional vectors."""
        assert EMBEDDING_DIMENSION_BGE_SMALL == 384

    def test_nomic_dimension_correct(self) -> None:
        """nomic-embed-text outputs 768-dimensional vectors."""
        assert EMBEDDING_DIMENSION_NOMIC == 768

    def test_dimensions_differ(self) -> None:
        assert EMBEDDING_DIMENSION_BGE_SMALL != EMBEDDING_DIMENSION_NOMIC


class TestTranscriptChunking:
    def test_max_tokens_positive(self) -> None:
        assert TRANSCRIPT_CHUNK_MAX_TOKENS > 0

    def test_overlap_less_than_max(self) -> None:
        assert TRANSCRIPT_OVERLAP_TOKENS < TRANSCRIPT_CHUNK_MAX_TOKENS

    def test_overlap_positive(self) -> None:
        assert TRANSCRIPT_OVERLAP_TOKENS >= 0


class TestRetrieval:
    def test_dense_top_k_positive(self) -> None:
        assert DENSE_TOP_K_DEFAULT > 0

    def test_rerank_top_k_lte_dense(self) -> None:
        """Reranker returns a subset of the initial retrieval."""
        assert RERANK_TOP_K_DEFAULT <= DENSE_TOP_K_DEFAULT

    def test_hybrid_alpha_in_range(self) -> None:
        assert 0.0 <= HYBRID_ALPHA_DEFAULT <= 1.0

    def test_bm25_params_positive(self) -> None:
        assert BM25_K1 > 0
        assert 0.0 < BM25_B <= 1.0


class TestQdrant:
    def test_collection_names_non_empty(self) -> None:
        assert len(QDRANT_TRANSCRIPT_COLLECTION) > 0
        assert len(QDRANT_FRAME_COLLECTION) > 0

    def test_collection_names_differ(self) -> None:
        assert QDRANT_TRANSCRIPT_COLLECTION != QDRANT_FRAME_COLLECTION


class TestLLM:
    def test_max_context_chunks_positive(self) -> None:
        assert LLM_MAX_CONTEXT_CHUNKS > 0

    def test_max_response_tokens_positive(self) -> None:
        assert LLM_MAX_RESPONSE_TOKENS > 0

    def test_temperature_in_range(self) -> None:
        assert 0.0 <= LLM_TEMPERATURE <= 2.0


class TestWhisper:
    def test_model_sizes_contains_base(self) -> None:
        assert "base" in WHISPER_MODEL_SIZES

    def test_model_sizes_non_empty(self) -> None:
        assert len(WHISPER_MODEL_SIZES) > 0


class TestPipelineStageNames:
    """All stage names must be non-empty strings — used in PipelineEvent."""

    def test_all_stage_names_non_empty(self) -> None:
        stages = [
            STAGE_METADATA_EXTRACTION,
            STAGE_AUDIO_EXTRACTION,
            STAGE_FRAME_EXTRACTION,
            STAGE_TRANSCRIPTION,
            STAGE_OCR,
            STAGE_OBJECT_DETECTION,
            STAGE_EMBEDDING,
            STAGE_VECTOR_UPSERT,
            STAGE_RETRIEVAL,
            STAGE_RERANKING,
            STAGE_GENERATION,
        ]
        for stage in stages:
            assert isinstance(stage, str), f"Stage {stage!r} must be a string"
            assert len(stage) > 0, "Stage name must not be empty"

    def test_all_stage_names_unique(self) -> None:
        """Stage names are used as event identifiers — they must be unique."""
        stages = [
            STAGE_METADATA_EXTRACTION,
            STAGE_AUDIO_EXTRACTION,
            STAGE_FRAME_EXTRACTION,
            STAGE_TRANSCRIPTION,
            STAGE_OCR,
            STAGE_OBJECT_DETECTION,
            STAGE_EMBEDDING,
            STAGE_VECTOR_UPSERT,
            STAGE_RETRIEVAL,
            STAGE_RERANKING,
            STAGE_GENERATION,
        ]
        assert len(stages) == len(set(stages)), "Stage names must be unique"
