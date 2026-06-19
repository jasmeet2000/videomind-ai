"""
Unit tests for app/domain/entities.py

Tests verify:
- Entities are pure Python dataclasses (no side effects on init)
- Default values are correct
- UUID generation is unique per instance
- Enumerations contain expected values
"""

from __future__ import annotations

from app.domain.entities import (
    Frame,
    Modality,
    PipelineEvent,
    SearchResult,
    TextBlock,
    TranscriptChunk,
    Video,
    VideoStatus,
)


class TestVideoStatus:
    def test_has_all_lifecycle_states(self) -> None:
        assert VideoStatus.PENDING == "pending"
        assert VideoStatus.PROCESSING == "processing"
        assert VideoStatus.COMPLETED == "completed"
        assert VideoStatus.FAILED == "failed"

    def test_is_string_enum(self) -> None:
        assert isinstance(VideoStatus.PENDING, str)


class TestModality:
    def test_has_all_pipeline_sources(self) -> None:
        assert Modality.AUDIO == "audio"
        assert Modality.VISUAL == "visual"
        assert Modality.OBJECT == "object"
        assert Modality.SCENE == "scene"


class TestVideo:
    def test_default_status_is_pending(self) -> None:
        video = Video()
        assert video.status == VideoStatus.PENDING

    def test_unique_id_per_instance(self) -> None:
        v1, v2 = Video(), Video()
        assert v1.id != v2.id

    def test_id_is_string(self) -> None:
        assert isinstance(Video().id, str)

    def test_default_resolution_is_zero(self) -> None:
        assert Video().resolution == (0, 0)

    def test_created_at_set_on_init(self) -> None:
        from datetime import datetime
        assert isinstance(Video().created_at, datetime)


class TestTranscriptChunk:
    def test_defaults(self) -> None:
        chunk = TranscriptChunk()
        assert chunk.text == ""
        assert chunk.confidence == 0.0
        assert chunk.language == "en"

    def test_unique_id(self) -> None:
        assert TranscriptChunk().id != TranscriptChunk().id

    def test_start_before_end(self) -> None:
        chunk = TranscriptChunk(start_seconds=10.0, end_seconds=15.0)
        assert chunk.start_seconds < chunk.end_seconds


class TestTextBlock:
    def test_defaults(self) -> None:
        block = TextBlock()
        assert block.text == ""
        assert block.confidence == 0.0
        assert block.bounding_box == (0, 0, 0, 0)

    def test_custom_values(self) -> None:
        block = TextBlock(text="Hello", confidence=0.95, bounding_box=(10, 20, 100, 50))
        assert block.text == "Hello"
        assert block.confidence == 0.95


class TestFrame:
    def test_defaults(self) -> None:
        frame = Frame()
        assert frame.ocr_blocks == []
        assert frame.objects_detected == []
        assert frame.scene_label == ""

    def test_unique_id(self) -> None:
        assert Frame().id != Frame().id

    def test_ocr_blocks_list_not_shared(self) -> None:
        """dataclass field(default_factory=list) must not share the same list."""
        f1, f2 = Frame(), Frame()
        f1.ocr_blocks.append(TextBlock(text="hello"))
        assert len(f2.ocr_blocks) == 0


class TestSearchResult:
    def test_defaults(self) -> None:
        result = SearchResult()
        assert result.score == 0.0
        assert result.modality == Modality.AUDIO
        assert result.metadata == {}

    def test_metadata_not_shared(self) -> None:
        r1, r2 = SearchResult(), SearchResult()
        r1.metadata["key"] = "value"
        assert "key" not in r2.metadata


class TestPipelineEvent:
    def test_defaults(self) -> None:
        event = PipelineEvent()
        assert event.success is True
        assert event.error_message == ""
        assert event.duration_ms == 0.0

    def test_failure_event(self) -> None:
        event = PipelineEvent(
            stage="ocr",
            video_id="vid-1",
            success=False,
            error_message="CUDA OOM",
        )
        assert not event.success
        assert event.error_message == "CUDA OOM"

    def test_timestamp_set_on_init(self) -> None:
        from datetime import datetime
        assert isinstance(PipelineEvent().timestamp, datetime)
