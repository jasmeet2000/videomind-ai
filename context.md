# VideoMind AI — Context (Quick Reference)
> Keep this file under 150 lines. Update after every phase.

---

## API Routes

| Method | Route | Description |
|---|---|---|
| GET | `/health` | Liveness check — returns `{ status: "ok" }` |
| GET | `/health/ready` | Readiness check — verifies DB + Qdrant connectivity |
| POST | `/api/v1/videos/upload` | Upload a video file; triggers async ingestion pipeline |
| GET | `/api/v1/videos/{video_id}` | Retrieve video metadata + processing status |
| POST | `/api/v1/search` | Semantic search across a video's indexed content |
| POST | `/api/v1/chat` | RAG-based Q&A against one or more videos |

---

## Folder Structure (Abbreviated)

```
videomind-ai/
├── app/
│   ├── api/          # Routes, schemas, DI dependencies
│   ├── core/         # Config, logging, exceptions, constants
│   ├── domain/       # Entities + ABCs (interfaces)
│   ├── video/        # FFmpeg extraction, OpenCV frames, metadata
│   ├── speech/       # Whisper STT, language detection
│   ├── vision/       # OCR (PaddleOCR/EasyOCR), object detection, scene
│   ├── embeddings/   # Embedding service + model registry
│   ├── retrieval/    # Dense, hybrid, reranker
│   ├── generation/   # Prompt builder, context builder, Ollama client
│   ├── repositories/ # PostgreSQL + Qdrant data access
│   └── use_cases/    # Ingest, search, chat orchestration
├── frontend/         # Streamlit app (Phase 9)
├── tests/            # unit/ and integration/
├── data/             # Uploaded videos (gitignored)
├── logs/             # Loguru output (gitignored)
└── docs/             # Architecture diagrams, ADRs
```

---

## Key CLI Commands

```bash
# Start full stack
docker-compose up --build

# Start only the FastAPI dev server (no Docker)
uvicorn app.main:app --reload --port 8000

# Run all tests
pytest tests/ -v

# Run linter
ruff check app/ tests/

# Sort imports
isort app/ tests/

# Run Streamlit frontend
streamlit run frontend/app.py
```

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/videomind` |
| `QDRANT_HOST` | Qdrant server host | `localhost` |
| `QDRANT_PORT` | Qdrant server port | `6333` |
| `OLLAMA_HOST` | Ollama server host | `http://localhost:11434` |
| `OLLAMA_MODEL` | Default LLM model name | `qwen3` |
| `EMBEDDING_MODEL` | HuggingFace model ID | `BAAI/bge-small-en-v1.5` |
| `WHISPER_MODEL` | Whisper model size | `base` |
| `LOG_LEVEL` | Loguru log level | `INFO` |
| `DATA_DIR` | Path to video upload directory | `./data` |
| `MAX_VIDEO_SIZE_MB` | Max upload size | `500` |

---

## Core Class Responsibilities

| Class | File | Responsibility |
|---|---|---|
| `Settings` | `core/config.py` | Pydantic BaseSettings — all env var config |
| `Video` | `domain/entities.py` | Core video entity with metadata |
| `Transcript` | `domain/entities.py` | Timestamped transcript chunk |
| `Frame` | `domain/entities.py` | Extracted video frame with OCR/object data |
| `SearchResult` | `domain/entities.py` | Retrieved chunk + score + timestamp |
| `IOCREngine` | `domain/interfaces.py` | ABC for OCR strategy implementations |
| `IEmbeddingModel` | `domain/interfaces.py` | ABC for embedding model implementations |
| `ILLMBackend` | `domain/interfaces.py` | ABC for LLM backend implementations |
| `VideoProcessor` | `video/extractor.py` | Composes FrameExtractor + AudioExtractor |
| `WhisperService` | `speech/whisper_service.py` | Transcription with word-level timestamps |
| `OCRService` | `vision/ocr_service.py` | Strategy selector for OCR engines |
| `PaddleOCRAdapter` | `vision/paddle_ocr.py` | Adapter for PaddleOCR wrapping into IOCREngine |
| `EasyOCRAdapter` | `vision/easy_ocr.py` | Adapter for EasyOCR wrapping into IOCREngine |
| `ObjectDetector` | `vision/object_detector.py` | Object detector using Mobilenet-SSD model |
| `SceneAnalyzer` | `vision/scene_analyzer.py` | Scene classifier using Mobilenet model |
| `EmbeddingService` | `embeddings/service.py` | Encodes text → vectors |
| `ModelRegistry` | `embeddings/registry.py` | Singleton + Factory for embedding models |
| `HybridRetriever` | `retrieval/hybrid.py` | Dense + BM25 sparse fusion |
| `LLMService` | `generation/llm_service.py` | Ollama client + response parsing |
| `IngestVideoUseCase` | `use_cases/ingest_video.py` | Orchestrates full ingestion pipeline |
| `SearchVideoUseCase` | `use_cases/search_video.py` | Handles semantic search |
| `ChatWithVideoUseCase` | `use_cases/chat_with_video.py` | Full RAG query flow |

---

## Naming Conventions

- Files: `snake_case.py`
- Classes: `PascalCase`
- Service classes: suffix `_service` (e.g., `WhisperService`)
- Repository classes: suffix `_repository` (e.g., `VideoRepository`)
- Use case classes: suffix `UseCase` (e.g., `IngestVideoUseCase`)
- Interface/ABC classes: prefix `I` (e.g., `IOCREngine`)
- Constants: `UPPER_SNAKE_CASE` in `core/constants.py`
- Pydantic schemas: suffix `Request`/`Response` (e.g., `UploadVideoRequest`)
