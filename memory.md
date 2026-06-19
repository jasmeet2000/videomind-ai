# VideoMind AI — Memory

> Maintained across all phases. Every decision made is logged here with its rationale.

---

## Project Vision & Goals

**Primary goal:** Build a production-grade multi-modal video intelligence platform that ingests videos and makes them fully queryable via natural language — 100% locally, using only free/open-source tools.

**Secondary goal:** The builder must be able to walk into any AI Engineer interview and explain every architectural decision from first principles, without notes.

**Non-negotiable constraints:**
- No paid APIs. No cloud dependencies.
- Everything runs on localhost via Docker.
- Presentable to hiring managers on GitHub.

---

## Architecture Decisions

### ADR-001: Clean Architecture as the structural backbone
- **Decision:** Use Clean Architecture (Presentation → API → Application → Service → Domain → Repository → Infrastructure).
- **Why:** Enforces strict separation of concerns, making each layer independently testable. Business logic never leaks into route handlers. Adding a new LLM backend, OCR engine, or database requires zero changes to the application/domain layers.
- **Alternatives rejected:** MVC (no clear seam for ML pipelines), flat structure (becomes unmanageable at scale), hexagonal/ports-and-adapters (same principle, more complex naming without benefit at this scale).

### ADR-002: FastAPI as the API layer
- **Decision:** FastAPI with Uvicorn as the ASGI server.
- **Why:** Native async support (important for IO-bound ML model calls), automatic OpenAPI docs, first-class Pydantic v2 integration, Python type hints are enforced at runtime via Pydantic validators.
- **Alternatives rejected:** Flask (no native async, no built-in validation), Django REST (too heavy, ORM-centric).

### ADR-003: Qdrant as the vector database
- **Decision:** Qdrant running in a local Docker container.
- **Why:** Supports hybrid search (dense + sparse BM25) natively, provides a Python client with batch upsert, runs fully locally, has a filterable metadata store baked in (so we can filter by video_id, timestamp range, modality). Named collections map cleanly to our domain model.
- **Alternatives rejected:** ChromaDB (no built-in sparse/hybrid), FAISS (in-memory only, no persistence without extra work), Weaviate (heavier, harder to self-host).

### ADR-004: PostgreSQL for metadata
- **Decision:** PostgreSQL for video metadata and transcript chunks.
- **Why:** Relational structure suits the video→chunks→embeddings hierarchy. JSONB columns give flexibility for per-chunk metadata. Well-understood, production-grade, runs in Docker.
- **Alternatives rejected:** SQLite (no concurrent writes, not production-grade), MongoDB (schema flexibility not needed here, relational joins are cleaner).

### ADR-005: Whisper for speech-to-text
- **Decision:** `openai/whisper-base` with `distil-whisper/distil-small.en` as a faster fallback.
- **Why:** Whisper is open-source, runs locally, produces word-level timestamps (critical for temporal indexing), supports multilingual audio, and achieves near-SOTA accuracy for a local model.
- **Alternatives rejected:** Wav2Vec2 (no timestamps), SpeechBrain (higher complexity), paid APIs (violates constraints).

### ADR-006: PaddleOCR primary, EasyOCR fallback (Strategy + Adapter)
- **Decision:** OCR engine is pluggable via the Strategy pattern. PaddleOCR is the default; EasyOCR activates when PaddleOCR confidence is below threshold.
- **Why:** PaddleOCR outperforms EasyOCR on dense text (slides, code) but EasyOCR handles rotated/stylized text better. Wrapping both in an Adapter means the caller never changes when we swap engines.
- **Alternatives rejected:** Tesseract (lower accuracy on printed/digital text), paid Vision APIs (violates constraints).

### ADR-007: BAAI/bge-small-en-v1.5 as the embedding model
- **Decision:** Primary embedding model is `BAAI/bge-small-en-v1.5`.
- **Why:** Tops MTEB benchmarks for its size class (384 dimensions), runs CPU-only, is sentence-transformers compatible, and is free. The registry is open to adding `nomic-embed-text` or other models later (Open/Closed Principle).
- **Alternatives rejected:** OpenAI embeddings (paid), all-MiniLM (lower quality).

### ADR-008: Ollama for local LLM serving
- **Decision:** Use Ollama to serve Qwen3, Llama 3.1, or Gemma 3 locally.
- **Why:** Ollama provides a single HTTP API regardless of which model is loaded. Swapping models requires zero code changes (Strategy + Factory pattern at the LLM service layer). Runs entirely offline.
- **Alternatives rejected:** llama.cpp directly (more setup, no unified API), HuggingFace Transformers (high VRAM requirement for generation, slower inference).

### ADR-009: Streamlit for the frontend (Phase 9)
- **Decision:** Defer Streamlit frontend to Phase 9.
- **Why (YAGNI):** Building a frontend before the backend is validated wastes time. Streamlit is chosen because it renders Python natively (no JS/CSS), supports file upload widgets, and chat-style interfaces, making it ideal for RAG demos.
- **Alternatives rejected:** React (unnecessary complexity for a demo tool), Gradio (less customizable).

### ADR-010: Docker Compose as the orchestration layer
- **Decision:** Single `docker-compose up` starts the full stack: FastAPI app, PostgreSQL, Qdrant, Ollama.
- **Why:** Eliminates "works on my machine" problems. Hiring managers can clone and run in one command. Satisfies 12-Factor App (stateless processes, config via env vars, logs to stdout).

### ADR-011: ASGI Lifespan over deprecated on_event hooks
- **Decision:** Use FastAPI's `@asynccontextmanager` lifespan pattern instead of `@app.on_event("startup")`.
- **Why:** `on_event` is deprecated since FastAPI 0.93. Lifespan keeps startup/shutdown co-located and is compatible with future async context manager patterns. Loguru is configured in startup, ensuring structured logging from the first request.

### ADR-012: Request-ID middleware for log correlation
- **Decision:** Every HTTP request receives a UUID4 `request_id`, attached via middleware, returned in `X-Request-ID` header, and bound to all Loguru log calls via `contextualize()`.
- **Why:** Production requirement. Without request IDs, correlating a single user request across 10+ log lines is impossible. The middleware approach means all route handlers get this for free.

### ADR-013: Pydantic v2 `SettingsConfigDict` over `class Config`
- **Decision:** Use `model_config = SettingsConfigDict(...)` in `Settings`.
- **Why:** `class Config` is deprecated in Pydantic v2 and emits warnings. `SettingsConfigDict` is the v2 canonical approach and provides type-safe config. Also added `extra="ignore"` to prevent failures when extra env vars are present (12-Factor: permissive env loading).

### ADR-014: Progressive coverage thresholds per phase
- **Decision:** Coverage `fail_under` starts at 50% (Phase 2), rising to 80% at Phase 10.
- **Why:** Stub files for Phases 3–8 contribute zero coverage but must exist for import resolution. Measuring only implemented files gives 92% at Phase 2 — but the threshold tracks overall project coverage to keep the build honest.

### ADR-015: Python 3.9 compatibility (`typing` module for dataclass fields)
- **Decision:** Use `from typing import List, Dict, Optional, Tuple` in dataclass field annotations.
- **Why:** Python 3.9 doesn't support `list[X]`, `dict[X, Y]`, `X | None` in runtime positions (dataclass fields, Pydantic fields). `from __future__ import annotations` defers evaluation for function signatures only — not for dataclass/Pydantic model class bodies. The `typing` module forms are safe in all Python 3.9+ contexts.

---

## Phase Completion Status

| Phase | Status | Notes |
|---|---|---|
| 1 | ✅ Complete | ADR, folder scaffold, memory.md, context.md, AGENTS.md |
| 2 | ✅ Complete | core/ module fully implemented; 153 tests pass; 91.8% coverage; app boots |
| 3 | ✅ Complete | video processing fully implemented (OpenCV/FFmpeg fallback, 91-93% coverage) |
| 4 | ✅ Complete | speech pipeline fully implemented (Whisper transcription, token-based chunking, language detection, 79-89% coverage) |
| 5 | ✅ Complete | OCR adapters (PaddleOCR/EasyOCR), object detection, scene analyzer fully implemented and tested (86.78% total coverage) |
| 6 | ✅ Complete | Embeddings + Qdrant |
| 7 | ✅ Complete | Retrieval layer (Dense, Sparse BM25, Hybrid, Reranker) |
| 8 | ⏳ Pending | LLM integration + RAG |
| 9 | ⏳ Pending | FastAPI routes + Streamlit |
| 10 | ⏳ Pending | Tests |
| 11 | ⏳ Pending | Docker + CI/CD |
| 12 | ⏳ Pending | README + final docs |

---

## Pending Tasks (Priority Order)

1. **Phase 7:** Implement `app/retrieval/` — Dense, Sparse, and Hybrid retrievers, plus CrossEncoder reranking.
2. Continue per phase table above.

---

## Known Issues & Blockers

- None at Phase 1 completion.

---

## Lessons Learned

- Phase 1: Clean Architecture's value isn't in naming layers — it's in the dependency rule: **inner layers never import from outer layers.** This is the single constraint that makes the whole system testable.

---

## Key Design Patterns Applied

| Pattern | Location | Justification |
|---|---|---|
| Strategy | `vision/ocr_service.py`, `generation/llm_service.py` | Swap OCR engines / LLM backends without changing callers |
| Factory | `embeddings/registry.py`, model loaders | Centralize and encapsulate construction logic |
| Repository | `repositories/` | Decouple persistence from business logic |
| Adapter | OCR engine wrappers | External APIs don't match internal `TextBlock` contract |
| Builder | `generation/prompt_builder.py` | Complex prompt construction step-by-step |
| Singleton | Embedding model registry, Qdrant client | Expensive to initialize; shared across all requests |
| Observer | Pipeline event hooks | Decouple monitoring/logging from processing logic |
