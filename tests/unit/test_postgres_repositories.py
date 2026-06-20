import pytest
import sys
from unittest.mock import AsyncMock, patch, MagicMock
from contextlib import asynccontextmanager

from app.domain.entities import Video, TranscriptChunk, Modality, VideoStatus
from app.repositories.postgres_video_repository import PostgresVideoRepository
from app.repositories.postgres_transcript_repository import PostgresTranscriptRepository


@pytest.fixture
def mock_asyncpg():
    mock_pool = MagicMock()
    mock_conn = AsyncMock()
    
    @asynccontextmanager
    async def transaction_mock():
        yield None
    mock_conn.transaction = transaction_mock
    
    @asynccontextmanager
    async def acquire_mock(*args, **kwargs):
        yield mock_conn

    mock_pool.acquire = acquire_mock
    
    mock_module = MagicMock()
    mock_module.create_pool = AsyncMock(return_value=mock_pool)
    
    with patch.dict("sys.modules", {"asyncpg": mock_module}):
        yield mock_conn


@pytest.mark.asyncio
async def test_postgres_video_repository(mock_asyncpg):
    repo = PostgresVideoRepository(dsn="postgres://fake")
    
    # 1. Save video
    vid = Video(id="vid1", filename="test.mp4")
    await repo.save(vid)
    mock_asyncpg.execute.assert_called()
    
    # 2. Get video
    mock_record = {
        "id": "vid1", "title": "test", "description": None,
        "filename": "test.mp4", "file_path": "/test/test.mp4", "status": "pending",
        "error_message": None, "duration_seconds": None,
        "created_at": "2023-01-01T00:00:00", "updated_at": "2023-01-01T00:00:00"
    }
    mock_asyncpg.fetchrow.return_value = mock_record
    
    fetched = await repo.get_by_id("vid1")
    assert fetched.id == "vid1"
    assert fetched.filename == "test.mp4"
    
    # 3. Missing video
    mock_asyncpg.fetchrow.return_value = None
    missing = await repo.get_by_id("vid999")
    assert missing is None


@pytest.mark.asyncio
async def test_postgres_transcript_repository(mock_asyncpg):
    repo = PostgresTranscriptRepository(dsn="postgres://fake")
    
    # 1. Save chunks
    chunks = [
        TranscriptChunk(id="c1", video_id="vid1", text="text1", start_seconds=0.0)
    ]
    await repo.save_batch(chunks)
    mock_asyncpg.executemany.assert_called_once()
    
    # 2. Get chunks
    mock_record = {
        "id": "c1", "video_id": "vid1", "text": "text1",
        "start_seconds": 0.0, "end_seconds": 1.0, "modality": "audio",
        "embedding": None
    }
    mock_asyncpg.fetch.return_value = [mock_record]
    
    fetched = await repo.get_by_video_id("vid1")
    assert len(fetched) == 1
    assert fetched[0].id == "c1"
    
    # 3. Delete chunks - Interface actually doesn't have delete_chunks_by_video_id
    # We will remove this test part because ITranscriptRepository doesn't define delete.

