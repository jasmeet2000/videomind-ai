import pytest
import sqlite3
import os

from app.domain.entities import Video, TranscriptChunk, Modality, VideoStatus
from app.repositories.sqlite_video_repository import SQLiteVideoRepository
from app.repositories.sqlite_transcript_repository import SQLiteTranscriptRepository


@pytest.fixture
def test_db_path(tmp_path):
    db_file = tmp_path / "test_videomind.db"
    return str(db_file)


@pytest.mark.asyncio
async def test_sqlite_video_repository(test_db_path):
    repo = SQLiteVideoRepository(db_path=test_db_path)
    
    # 1. Create a video
    video = Video(
        id="vid123",
        title="Test Video",
        description="A test",
        filename="test.mp4",
        status=VideoStatus.PROCESSING
    )
    await repo.save(video)
    
    # 2. Get the video
    fetched = await repo.get_by_id("vid123")
    assert fetched is not None
    assert fetched.title == "Test Video"
    assert fetched.status == VideoStatus.PROCESSING
    
    # 3. Update the video
    fetched.status = VideoStatus.COMPLETED
    fetched.duration_seconds = 120.5
    await repo.save(fetched)
    
    # 4. Fetch again and verify updates
    updated = await repo.get_by_id("vid123")
    assert updated.status == VideoStatus.COMPLETED
    assert updated.duration_seconds == 120.5
    
    # 5. Get missing video
    missing = await repo.get_by_id("vid999")
    assert missing is None


@pytest.mark.asyncio
async def test_sqlite_transcript_repository(test_db_path):
    # Need to initialize video repo first so the videos table exists (foreign key)
    vid_repo = SQLiteVideoRepository(db_path=test_db_path)
    
    vid = Video(id="vid1", title="test", filename="test.mp4")
    await vid_repo.save(vid)

    repo = SQLiteTranscriptRepository(db_path=test_db_path)
    
    # 1. Create chunks
    chunks = [
        TranscriptChunk(
            id="c1",
            video_id="vid1",
            text="Hello world",
            start_seconds=0.0,
            end_seconds=2.5,
            modality=Modality.AUDIO
        ),
        TranscriptChunk(
            id="c2",
            video_id="vid1",
            text="Visual text",
            start_seconds=2.5,
            end_seconds=None,
            modality=Modality.VISUAL
        )
    ]
    
    await repo.save_chunks(chunks)
    
    # 2. Retrieve chunks
    fetched_chunks = await repo.get_chunks_by_video_id("vid1")
    assert len(fetched_chunks) == 2
    assert fetched_chunks[0].text == "Hello world"
    assert fetched_chunks[1].modality == Modality.VISUAL
    
    # 3. Delete chunks
    await repo.delete_chunks_by_video_id("vid1")
    empty_chunks = await repo.get_chunks_by_video_id("vid1")
    assert len(empty_chunks) == 0
