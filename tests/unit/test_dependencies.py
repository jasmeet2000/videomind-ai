import pytest
import sys
from unittest.mock import patch, AsyncMock, MagicMock
from contextlib import ExitStack

from app.api.dependencies.services import (
    get_db,
    get_qdrant_client,
    get_ingest_use_case,
    get_search_use_case,
    get_chat_use_case,
)


@pytest.mark.asyncio
async def test_get_db_with_mocked_pool():
    """Test that get_db yields a connection when asyncpg pool is mocked."""
    mock_conn = AsyncMock()
    mock_acquire_context = AsyncMock()
    mock_acquire_context.__aenter__.return_value = mock_conn
    mock_acquire_context.__aexit__.return_value = None
    
    mock_pool = MagicMock()
    mock_pool.acquire.return_value = mock_acquire_context

    # We need to mock the asyncpg module since it's lazy-imported
    mock_asyncpg = MagicMock()
    mock_asyncpg.create_pool = AsyncMock(return_value=mock_pool)

    with patch.dict("sys.modules", {"asyncpg": mock_asyncpg}), \
         patch("app.api.dependencies.services.settings") as mock_settings:
        
        mock_settings.database_url = "postgresql://user:pass@localhost:5432/db"
        
        # Reset global to allow recreation
        import app.api.dependencies.services as srv
        srv._db_pool = None
        
        # We must use async for to consume the async generator
        async for conn in get_db():
            assert conn is mock_conn
            
        mock_asyncpg.create_pool.assert_called_once()


def test_get_qdrant_client_singleton():
    """Test that get_qdrant_client returns the same instance on multiple calls."""
    with patch("app.repositories.qdrant_vector_repository.QdrantVectorRepository") as mock_qdrant_cls:
        mock_instance = mock_qdrant_cls.return_value
        
        # Reset global state
        import app.api.dependencies.services as srv
        srv._qdrant_client = None
        
        client1 = get_qdrant_client()
        client2 = get_qdrant_client()
        
        assert client1 is mock_instance
        assert client2 is mock_instance
        # Should only be instantiated once
        mock_qdrant_cls.assert_called_once()


def test_dependency_injection_wiring():
    """
    Test that the use case dependency injection functions can be executed and
    instantiate their respective classes without throwing errors.
    """
    patches = [
        "app.repositories.qdrant_vector_repository.QdrantVectorRepository",
        "app.repositories.sqlite_video_repository.SQLiteVideoRepository",
        "app.repositories.sqlite_transcript_repository.SQLiteTranscriptRepository",
        "app.repositories.postgres_video_repository.PostgresVideoRepository",
        "app.repositories.postgres_transcript_repository.PostgresTranscriptRepository",
        "app.repositories.in_memory_video_repository.InMemoryVideoRepository",
        "app.repositories.in_memory_transcript_repository.InMemoryTranscriptRepository",
        "app.speech.whisper_service.WhisperService",
        "app.video.processor.VideoProcessor",
        "app.use_cases.ingest_video.IngestVideoUseCase",
        "app.use_cases.search_video.SearchVideoUseCase",
        "app.use_cases.chat_with_video.ChatWithVideoUseCase",
        "app.retrieval.dense.DenseRetriever",
        "app.retrieval.sparse.BM25SparseRetriever",
        "app.retrieval.hybrid.HybridRetriever",
        "app.retrieval.reranker.CrossEncoderReranker",
        "app.embeddings.service.EmbeddingService",
        "app.generation.llm_service.OllamaClient",
        "app.generation.context_builder.ContextBuilder",
        "app.generation.prompt_builder.PromptBuilder",
    ]
    
    with ExitStack() as stack:
        for p in patches:
            stack.enter_context(patch(p))

        # Test use cases
        assert get_ingest_use_case() is not None
        assert get_search_use_case() is not None
        assert get_chat_use_case() is not None
