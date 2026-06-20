import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from fastapi.testclient import TestClient
from app.main import create_app
from app.api.schemas.search import SearchResponse, ChatResponse
from app.domain.entities import VideoStatus

# Create a test app instance
app = create_app()
client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@patch("app.api.routes.video._run_ingestion")
def test_upload_video(mock_ingestion):
    # Create a dummy file
    file_content = b"fake video content"
    files = {"file": ("test_vid.mp4", file_content, "video/mp4")}
    
    response = client.post("/api/v1/videos/upload", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert "video_id" in data
    assert data["status"] == "pending" or data["status"] == "processing"
    
    # Ensure the background task was dispatched
    # Wait, background tasks in TestClient are executed synchronously or mocked depending on setup.
    # In FastAPI's TestClient, background tasks run synchronously after the response!
    # Because we patched _run_ingestion, it was called synchronously.
    mock_ingestion.assert_called_once()


def test_get_video_status_not_found():
    response = client.get("/api/v1/videos/nonexistent/status")
    assert response.status_code == 200
    assert response.json()["status"] == "pending"


@pytest.mark.asyncio
async def test_search_route_with_mocked_usecase():
    mock_use_case = AsyncMock()
    mock_use_case.execute.return_value = [
        {"chunk_id": "c1", "text": "test text", "score": 0.9, "start_seconds": 10, "modality": "audio"}
    ]
    
    with patch("app.api.routes.search.get_search_use_case", return_value=mock_use_case, create=True), \
         patch("app.api.dependencies.services.get_search_use_case", return_value=mock_use_case):
        response = client.post("/api/v1/search", json={"query": "test", "video_id": "vid1", "top_k": 5})
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_results"] == 1
        assert data["results"][0]["text"] == "test text"
        assert data["results"][0]["timestamp_label"] == "00:10"


@pytest.mark.asyncio
async def test_chat_route_with_mocked_usecase():
    mock_use_case = AsyncMock()
    mock_use_case.execute.return_value = {
        "answer": "This is a test answer.",
        "sources": [{"chunk_id": "c1", "text": "source text", "score": 0.8, "start_seconds": 20}]
    }
    
    with patch("app.api.routes.chat.get_chat_use_case", return_value=mock_use_case, create=True), \
         patch("app.api.dependencies.services.get_chat_use_case", return_value=mock_use_case):
        response = client.post("/api/v1/chat", json={"question": "test question", "video_id": "vid1"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "This is a test answer."
        assert len(data["sources"]) == 1
        assert data["sources"][0]["timestamp_label"] == "00:20"

