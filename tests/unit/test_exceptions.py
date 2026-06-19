"""
Unit tests for app/core/exceptions.py

Tests verify:
- Each exception class carries the correct HTTP status code
- Message formatting is correct
- All exceptions inherit from VideoMindError
- Specific context attributes are set (e.g., video_id, stage)

Production requirement:
    FastAPI exception handlers catch VideoMindError and return the
    status_code to the client. These tests confirm the codes are correct
    so route handlers never accidentally return 200 on an error.
"""

from __future__ import annotations

from app.core.exceptions import (
    ConfigurationError,
    EmbeddingModelNotFoundError,
    FrameExtractionError,
    InvalidVideoFormatError,
    LLMUnavailableError,
    OCREngineUnavailableError,
    PromptBuildError,
    TranscriptionError,
    VectorSearchError,
    VideoMindError,
    VideoNotFoundError,
    VideoProcessingError,
)


class TestVideoMindError:
    """Base exception carries message and status code."""

    def test_is_exception_subclass(self) -> None:
        err = VideoMindError("test", status_code=500)
        assert isinstance(err, Exception)

    def test_message_stored(self) -> None:
        err = VideoMindError("something went wrong", status_code=400)
        assert err.message == "something went wrong"

    def test_status_code_stored(self) -> None:
        err = VideoMindError("msg", status_code=422)
        assert err.status_code == 422

    def test_default_status_code_is_500(self) -> None:
        err = VideoMindError("msg")
        assert err.status_code == 500

    def test_str_representation(self) -> None:
        err = VideoMindError("test message", status_code=500)
        assert "test message" in str(err)


class TestVideoNotFoundError:
    """404 for missing video resources."""

    def test_status_code_is_404(self) -> None:
        err = VideoNotFoundError("abc-123")
        assert err.status_code == 404

    def test_video_id_in_message(self) -> None:
        err = VideoNotFoundError("abc-123")
        assert "abc-123" in err.message

    def test_video_id_attribute(self) -> None:
        err = VideoNotFoundError("vid-999")
        assert err.video_id == "vid-999"

    def test_is_videomind_error(self) -> None:
        err = VideoNotFoundError("x")
        assert isinstance(err, VideoMindError)


class TestInvalidVideoFormatError:
    """422 Unprocessable Entity for bad uploads — Fail Fast principle."""

    def test_status_code_is_422(self) -> None:
        err = InvalidVideoFormatError("clip.exe", "unsupported format")
        assert err.status_code == 422

    def test_filename_in_message(self) -> None:
        err = InvalidVideoFormatError("clip.exe", "unsupported format")
        assert "clip.exe" in err.message

    def test_reason_in_message(self) -> None:
        err = InvalidVideoFormatError("video.mp4", "file is corrupted")
        assert "file is corrupted" in err.message


class TestVideoProcessingError:
    """500 when a pipeline stage fails."""

    def test_status_code_is_500(self) -> None:
        err = VideoProcessingError("transcription", "vid-1", "OOM error")
        assert err.status_code == 500

    def test_stage_attribute(self) -> None:
        err = VideoProcessingError("ocr", "vid-1", "reason")
        assert err.stage == "ocr"

    def test_video_id_attribute(self) -> None:
        err = VideoProcessingError("ocr", "vid-42", "reason")
        assert err.video_id == "vid-42"

    def test_all_fields_in_message(self) -> None:
        err = VideoProcessingError("embedding", "vid-7", "CUDA OOM")
        assert "embedding" in err.message
        assert "vid-7" in err.message
        assert "CUDA OOM" in err.message


class TestTranscriptionError:
    def test_status_code_is_500(self) -> None:
        assert TranscriptionError("vid-1", "model failed").status_code == 500

    def test_is_videomind_error(self) -> None:
        assert isinstance(TranscriptionError("v", "r"), VideoMindError)


class TestOCREngineUnavailableError:
    def test_status_code_is_503(self) -> None:
        assert OCREngineUnavailableError().status_code == 503

    def test_message_is_descriptive(self) -> None:
        err = OCREngineUnavailableError()
        assert len(err.message) > 0


class TestFrameExtractionError:
    def test_status_code_is_500(self) -> None:
        assert FrameExtractionError("vid-1", "codec error").status_code == 500


class TestEmbeddingModelNotFoundError:
    def test_status_code_is_500(self) -> None:
        err = EmbeddingModelNotFoundError("unknown-model")
        assert err.status_code == 500

    def test_model_name_in_message(self) -> None:
        err = EmbeddingModelNotFoundError("my-model")
        assert "my-model" in err.message


class TestVectorSearchError:
    def test_status_code_is_503(self) -> None:
        assert VectorSearchError("timeout").status_code == 503


class TestLLMUnavailableError:
    def test_status_code_is_503(self) -> None:
        assert LLMUnavailableError("connection refused").status_code == 503


class TestPromptBuildError:
    def test_status_code_is_500(self) -> None:
        assert PromptBuildError("missing query").status_code == 500


class TestConfigurationError:
    def test_status_code_is_500(self) -> None:
        err = ConfigurationError("DATABASE_URL", "missing value")
        assert err.status_code == 500

    def test_variable_name_in_message(self) -> None:
        err = ConfigurationError("DATABASE_URL", "missing value")
        assert "DATABASE_URL" in err.message


class TestExceptionHierarchy:
    """All domain exceptions must be catchable as VideoMindError."""

    def test_all_exceptions_inherit_from_base(self) -> None:
        """
        This test is critical for the FastAPI exception handler.
        A single handler for VideoMindError must catch ALL domain errors.
        """
        exceptions_to_test = [
            VideoNotFoundError("vid-1"),
            InvalidVideoFormatError("f.avi", "bad codec"),
            VideoProcessingError("stage", "vid-1", "reason"),
            TranscriptionError("vid-1", "reason"),
            OCREngineUnavailableError(),
            FrameExtractionError("vid-1", "reason"),
            EmbeddingModelNotFoundError("model"),
            VectorSearchError("reason"),
            LLMUnavailableError("reason"),
            PromptBuildError("reason"),
            ConfigurationError("VAR", "reason"),
        ]
        for exc in exceptions_to_test:
            assert isinstance(exc, VideoMindError), (
                f"{type(exc).__name__} must inherit from VideoMindError"
            )

    def test_all_exceptions_have_status_code(self) -> None:
        """Every domain exception must have a non-None status_code."""
        exceptions = [
            VideoNotFoundError("v"),
            InvalidVideoFormatError("f", "r"),
            VideoProcessingError("s", "v", "r"),
            OCREngineUnavailableError(),
            LLMUnavailableError("r"),
        ]
        for exc in exceptions:
            assert exc.status_code is not None
            assert isinstance(exc.status_code, int)
