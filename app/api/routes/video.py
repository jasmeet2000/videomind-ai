"""
VideoMind AI — Video API Routes (Phase 9)
============================================
Upload videos and check processing status.

SOLID — Single Responsibility:
    Routes handle HTTP concerns only. Business logic lives in use cases.
"""

from __future__ import annotations

import os
import uuid

from fastapi import APIRouter, BackgroundTasks, File, Request, UploadFile

from app.api.schemas.video import (
    UploadVideoResponse,
    VideoStatusResponse,
)
from app.core.config import get_settings
from app.core.logging import get_logger
from app.domain.entities import VideoStatus

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter()


@router.post("/upload", response_model=UploadVideoResponse)
async def upload_video(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """
    Upload a video file and start asynchronous processing.

    The file is saved to DATA_DIR and the IngestVideoUseCase is
    dispatched as a FastAPI background task.
    """
    video_id = str(uuid.uuid4())

    # Ensure data directory exists
    data_dir = settings.data_dir
    os.makedirs(data_dir, exist_ok=True)

    # Save the uploaded file
    filename = file.filename or f"{video_id}.mp4"
    file_path = os.path.join(data_dir, f"{video_id}_{filename}")

    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    logger.info("Video uploaded", video_id=video_id, filename=filename)

    # Store processing state in app.state for polling
    if not hasattr(request.app.state, "video_status"):
        request.app.state.video_status = {}

    request.app.state.video_status[video_id] = {
        "status": VideoStatus.PROCESSING,
        "progress_message": "Starting ingestion pipeline...",
        "filename": filename,
        "file_path": file_path,
    }

    # Dispatch background processing
    background_tasks.add_task(
        _run_ingestion, request.app, video_id, file_path
    )

    return UploadVideoResponse(
        video_id=video_id,
        status=VideoStatus.PROCESSING,
        message="Video accepted for processing.",
    )


@router.get("/{video_id}/status", response_model=VideoStatusResponse)
async def get_video_status(video_id: str, request: Request):
    """Poll the processing status of an uploaded video."""
    status_store = getattr(request.app.state, "video_status", {})
    entry = status_store.get(video_id)

    if entry is None:
        return VideoStatusResponse(
            video_id=video_id,
            status=VideoStatus.PENDING,
            progress_message="Video not found or not yet uploaded.",
        )

    return VideoStatusResponse(
        video_id=video_id,
        status=entry["status"],
        progress_message=entry.get("progress_message", ""),
    )


async def _run_ingestion(app, video_id: str, file_path: str) -> None:
    """Background task that runs the full ingestion pipeline."""
    status_store = getattr(app.state, "video_status", {})
    try:
        from app.api.dependencies.services import get_ingest_use_case

        use_case = get_ingest_use_case()

        status_store[video_id]["progress_message"] = "Extracting audio..."
        status_store[video_id]["status"] = VideoStatus.PROCESSING

        result = await use_case.execute(file_path, video_id)

        status_store[video_id]["status"] = VideoStatus.COMPLETED
        status_store[video_id]["progress_message"] = (
            f"Processing complete. {result.get('ingested_chunks', 0)} chunks ingested."
        )
        logger.info("Ingestion complete", video_id=video_id, result=result)

    except Exception as exc:
        status_store[video_id]["status"] = VideoStatus.FAILED
        status_store[video_id]["progress_message"] = f"Processing failed: {exc}"
        logger.error("Ingestion failed", video_id=video_id, error=str(exc))
