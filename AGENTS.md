# VideoMind AI — Agent Instructions (AGENTS.md)

> This file is written for any AI agent (or human) continuing this project.
> Read this FIRST before writing or modifying any code.

---

## The #1 Rule: The Dependency Direction

Inner layers **never** import from outer layers. The permitted import direction is:

```
Infrastructure → Repository → Domain ← Service ← Application ← API ← Presentation
```

Concretely:
- `domain/` imports NOTHING from this project (only stdlib and third-party)
- `video/`, `speech/`, `vision/`, `embeddings/`, `retrieval/`, `generation/` can import from `domain/` and `core/`
- `repositories/` can import from `domain/` and `core/`
- `use_cases/` can import from service layers, repositories, and domain
- `api/` can import from `use_cases/`, `core/`, and `domain/` schemas only
- `api/routes/` NEVER imports from service layers directly — always through use cases

**Violation of this rule = circular import risk and breaks testability.**

---

## Layer Responsibilities (What Lives Where)

| Layer | Directory | What goes here | What NEVER goes here |
|---|---|---|---|
| Presentation | `frontend/` | Streamlit UI widgets, session state | Any ML model calls |
| API | `app/api/` | Route handlers, request parsing, response formatting | Business logic |
| Application | `app/use_cases/` | Orchestration of services, transaction boundaries | Direct DB queries, model loading |
| Service | `app/video/`, `app/speech/`, etc. | ML model calls, data transformation | HTTP handling, DB queries |
| Domain | `app/domain/` | Entities, value objects, ABCs (interfaces) | Any implementation |
| Repository | `app/repositories/` | SQL queries, Qdrant upserts/searches | Business rules |
| Infrastructure | Config, model files, Docker | Environment wiring | Business logic |

---

## Naming Conventions

```
Files:          snake_case.py
Classes:        PascalCase
Services:       FooService         (e.g., WhisperService, OCRService)
Repositories:   FooRepository      (e.g., VideoRepository)
Use Cases:      FooUseCase         (e.g., IngestVideoUseCase)
Interfaces/ABCs: IFoo              (e.g., IOCREngine, IEmbeddingModel)
Pydantic schemas: FooRequest, FooResponse
Constants:      UPPER_SNAKE_CASE   (in core/constants.py only)
```

---

## How to Add a New OCR Engine

1. Create a new file in `app/vision/` (e.g., `tesseract_engine.py`)
2. Implement the `IOCREngine` ABC from `app/domain/interfaces.py`
3. The class must implement `extract(image: np.ndarray) -> List[TextBlock]`
4. Register it in `app/vision/ocr_service.py` in the strategy selector dict
5. Add a corresponding test in `tests/unit/test_ocr_service.py`
6. Update `context.md` with the new class

---

## How to Add a New Embedding Model

1. Create a new class implementing `IEmbeddingModel` from `app/domain/interfaces.py`
2. Register it in `app/embeddings/registry.py` (the Singleton+Factory registry)
3. The `EMBEDDING_MODEL` env var in `.env` selects which model to load
4. Do NOT modify `EmbeddingService` — it depends on the `IEmbeddingModel` interface (Open/Closed Principle)

---

## How to Add a New LLM Backend

1. Create a new class implementing `ILLMBackend` from `app/domain/interfaces.py`
2. The class must implement `generate(prompt: str) -> str`
3. Register it in `app/generation/llm_service.py` using the Strategy pattern
4. Select via `OLLAMA_MODEL` or a new env var

---

## How to Add a New API Route

1. Create or add to a file in `app/api/routes/`
2. Route handler ONLY: parse input → call a use case → return output
3. Create corresponding Pydantic schemas in `app/api/schemas/`
4. Register the router in `app/main.py`
5. Update `context.md` API Routes table

---

## Testing Requirements Per Layer

| Layer | Test type | How to mock |
|---|---|---|
| `domain/` | Unit | No mocks needed — pure Python |
| `video/`, `speech/`, `vision/` | Unit | Mock file I/O and model calls |
| `embeddings/`, `retrieval/` | Unit | Mock model outputs and Qdrant client |
| `repositories/` | Unit | Use `unittest.mock` to mock DB clients |
| `use_cases/` | Unit | Mock all service and repository dependencies |
| `api/routes/` | Integration | Use FastAPI `TestClient`, mock use cases |
| Full pipeline | Integration | Use real Docker stack (Qdrant + PostgreSQL) |

---

## Updating memory.md and context.md

After every phase or significant change:

**memory.md:**
- Append a new ADR entry under "Architecture Decisions" if a significant decision was made
- Update phase status table
- Add any new blockers or lessons learned

**context.md:**
- Add any new API routes to the routes table
- Add any new classes to the class responsibilities table
- Update CLI commands if new ones are introduced
- Keep the file under 150 lines — prune stale entries

---

## What NOT To Do

- ❌ Never put logic in route handlers (`app/api/routes/`)
- ❌ Never import from outer layers in inner layers (no `domain/` importing from `use_cases/`)
- ❌ Never create God classes (>5 public methods → split it)
- ❌ Never exceed ~150 lines per file (split into focused modules)
- ❌ Never use bare `except:` — always catch specific exception types
- ❌ Never hardcode magic numbers — use `core/constants.py`
- ❌ Never leave `# TODO` in committed code — open a GitHub Issue
- ❌ Never instantiate ML models inside route handlers or use cases — use the registry/factory
- ❌ Never expose stack traces to API clients — use custom exception handlers
- ❌ Never skip type hints on function signatures

---

## Monitoring Hooks

Each pipeline stage emits timing metrics via the Observer pattern. Use the `PipelineEvent` dataclass (defined in `domain/entities.py`) to emit events. The event bus is in `core/events.py` (to be created in Phase 2 or 3). Do not add timing logic inline in service methods — emit events instead.

---

## Docker Environment Notes

The full stack runs via `docker-compose up`. Services:
- `app`: FastAPI on port 8000
- `db`: PostgreSQL on port 5432
- `qdrant`: Qdrant on port 6333
- `ollama`: Ollama on port 11434

Wait-for-it logic should be implemented in the `app` service entrypoint to prevent startup race conditions with the database.
