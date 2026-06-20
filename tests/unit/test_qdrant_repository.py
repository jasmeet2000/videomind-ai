from unittest.mock import MagicMock, patch

import pytest

from app.repositories.qdrant_vector_repository import QdrantVectorRepository


@pytest.fixture
def mock_qdrant_client():
    mock_client = MagicMock()
    mock_module = MagicMock()
    mock_module.QdrantClient = MagicMock(return_value=mock_client)
    mock_module.models = MagicMock()

    with patch.dict("sys.modules", {"qdrant_client": mock_module}):
        yield mock_client


@pytest.mark.asyncio
async def test_qdrant_upsert_embeddings(mock_qdrant_client):
    repo = QdrantVectorRepository(host="localhost", port=6333, collection="test_col")

    points = [{"id": "c1", "vector": [0.1, 0.2], "payload": {"video_id": "vid1", "text": "hello"}}]

    await repo.upsert(points, collection="test_col")

    mock_qdrant_client.upsert.assert_called_once()
    args, kwargs = mock_qdrant_client.upsert.call_args
    assert kwargs["collection_name"] == "test_col"


@pytest.mark.asyncio
async def test_qdrant_search(mock_qdrant_client):
    # Setup mock response
    mock_hit = MagicMock()
    mock_hit.id = "c1"
    mock_hit.score = 0.85
    mock_hit.payload = {"video_id": "vid1", "text": "hello"}
    mock_resp = MagicMock()
    mock_resp.points = [mock_hit]
    mock_qdrant_client.query_points.return_value = mock_resp

    repo = QdrantVectorRepository(host="localhost", port=6333, collection="test_col")

    results = await repo.search(vector=[0.1, 0.2], video_id="vid1", top_k=5)

    mock_qdrant_client.query_points.assert_called_once()
    assert len(results) == 1
    assert results[0].chunk_id == "c1"
    assert results[0].score == 0.85
