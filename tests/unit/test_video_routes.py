import tempfile
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from app.api.routes.video import _run_ingestion, router
from app.domain.entities import VideoStatus

app = FastAPI()
app.include_router(router, prefix="/video")
client = TestClient(app)


def test_upload_video():
    with patch("app.api.dependencies.services.get_ingest_use_case") as mock_get_uc:
        use_case = AsyncMock()
        use_case.execute = AsyncMock(return_value={"ingested_chunks": 10})
        mock_get_uc.return_value = use_case

        # Create a dummy file
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tf:
            tf.write(b"dummy content")
            tf.flush()

            with open(tf.name, "rb") as f:
                response = client.post(
                    "/video/upload", files={"file": ("test.mp4", f, "video/mp4")}
                )

        assert response.status_code == 200
        data = response.json()
        assert "video_id" in data
        assert data["status"] == "processing"

        # Test status endpoint
        video_id = data["video_id"]
        status_response = client.get(f"/video/{video_id}/status")
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "completed"


def test_video_status_not_found():
    response = client.get("/video/invalid_id/status")
    assert response.status_code == 200
    assert response.json()["status"] == "pending"
    assert "not found" in response.json()["progress_message"]


@pytest.mark.asyncio
async def test_run_ingestion_success():
    with patch(
        "app.use_cases.ingest_video.IngestVideoUseCase.execute", new_callable=AsyncMock
    ) as mock_execute:
        mock_execute.return_value = {"ingested_chunks": 5}

        dummy_app = FastAPI()
        dummy_app.state.video_status = {"vid1": {"status": VideoStatus.PENDING}}

        await _run_ingestion(dummy_app, "vid1", "dummy.mp4")

        assert dummy_app.state.video_status["vid1"]["status"] == VideoStatus.COMPLETED


@pytest.mark.asyncio
async def test_run_ingestion_failure():
    with patch(
        "app.use_cases.ingest_video.IngestVideoUseCase.execute", new_callable=AsyncMock
    ) as mock_execute:
        mock_execute.side_effect = Exception("Failed")

        dummy_app = FastAPI()
        dummy_app.state.video_status = {"vid2": {"status": VideoStatus.PENDING}}

        await _run_ingestion(dummy_app, "vid2", "dummy.mp4")

        assert dummy_app.state.video_status["vid2"]["status"] == VideoStatus.FAILED
        assert "Failed" in dummy_app.state.video_status["vid2"]["progress_message"]
