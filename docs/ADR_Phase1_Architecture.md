# VideoMind AI — Architecture Decision Record (ADR)
# Phase 1 Deliverable

> **Author:** VideoMind AI Build System  
> **Date:** Phase 1  
> **Status:** Approved — Proceed to Phase 2

---

## What This Document Is

An Architecture Decision Record (ADR) captures **why** a system was built the way it was, not just **what** was built. Each decision records: the context, the options considered, the choice made, and the consequences. This document is a study guide — if you can explain every section here without reading it, you are ready for any AI Engineer interview.

---

## Part 1: Why Clean Architecture?

### The Problem We're Solving

VideoMind AI is a multi-modal AI system. It has ML models (Whisper, PaddleOCR, YOLO, bge-small), two databases (PostgreSQL, Qdrant), an LLM backend (Ollama), a REST API (FastAPI), and a frontend (Streamlit). Without architecture, this becomes a tangle of direct dependencies: route handlers calling Whisper directly, Whisper outputting to PostgreSQL directly, PostgreSQL queries littering everywhere.

**The result of no architecture:** you cannot test anything in isolation, you cannot swap Whisper for a better model, and you cannot explain the system to anyone.

### The Clean Architecture Solution

Clean Architecture, introduced by Robert C. Martin, imposes a single inviolable rule:

> **The Dependency Rule:** Source code dependencies can only point inward. Nothing in an inner layer can know anything about an outer layer.

```
┌─────────────────────────────────────────────────┐
│  Presentation (Streamlit)                       │
│  ┌───────────────────────────────────────────┐  │
│  │  API Layer (FastAPI routes, schemas)      │  │
│  │  ┌─────────────────────────────────────┐  │  │
│  │  │  Application Layer (Use Cases)      │  │  │
│  │  │  ┌───────────────────────────────┐  │  │  │
│  │  │  │  Service Layer (ML pipelines) │  │  │  │
│  │  │  │  ┌───────────────────────┐    │  │  │  │
│  │  │  │  │  Domain Layer         │    │  │  │  │
│  │  │  │  │  (Entities, ABCs)     │    │  │  │  │
│  │  │  │  └───────────────────────┘    │  │  │  │
│  │  │  │  Repository Layer             │  │  │  │
│  │  │  │  (DB abstraction)             │  │  │  │
│  │  │  └───────────────────────────────┘  │  │  │
│  │  │  Infrastructure (Docker, DB clients)│  │  │
│  │  └─────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
        Dependencies all point INWARD ←←←
```

### Why Each Layer Exists

| Layer | Directory | Purpose | Why it must be separate |
|---|---|---|---|
| **Domain** | `app/domain/` | Core entities (Video, Transcript, Frame) and ABCs (interfaces) | Must be dependency-free. If domain imports from a service, you can't test domain in isolation. |
| **Service** | `app/video/`, `app/speech/`, etc. | ML model calls, data transformation | One service per pipeline stage. OCRService doesn't know about Whisper. |
| **Repository** | `app/repositories/` | All SQL and Qdrant operations | Swap PostgreSQL for MongoDB → only this layer changes. Use cases never break. |
| **Application** | `app/use_cases/` | Orchestration: "do these steps in this order" | If orchestration lived in routes, routes would be untestable 500-line monsters. |
| **API** | `app/api/` | Parse HTTP input, call use case, format HTTP output | Routes should be 10 lines max. No `if` statements, no ML logic. |
| **Presentation** | `frontend/` | Streamlit widgets | UI can change completely without touching a single backend file. |

### What Alternatives Were Rejected and Why

**MVC (Model-View-Controller):**  
MVC works for CRUD apps with a thin model layer. Our "model" layer would be enormous (Whisper + OCR + YOLO + embeddings + Qdrant). MVC provides no guidance on how to organize ML pipelines, no seam between "business logic" and "ML inference."

**Flat structure (all files in one directory):**  
Works for scripts. Fails at scale. Import cycles become unavoidable. You cannot test one component without loading the entire app.

**Hexagonal (Ports & Adapters):**  
Same principle as Clean Architecture with different naming (ports = interfaces, adapters = implementations). We chose Clean Architecture's naming because it maps more directly to how we describe the system in interviews and documentation.

---

## Part 2: SOLID Principles — Specific Locations

### Single Responsibility Principle (SRP)
*Each class does exactly one thing.*

| Class | What it does | What it explicitly does NOT do |
|---|---|---|
| `AudioExtractor` | Extracts audio from video | Does not transcribe, does not save metadata |
| `WhisperService` | Transcribes audio to text | Does not extract audio, does not save chunks |
| `OCRService` | Selects engine, extracts text | Does not detect objects, does not embed text |
| `EmbeddingService` | Encodes text to vectors | Does not store vectors, does not retrieve |
| `PromptBuilder` | Assembles prompt string | Does not call LLM, does not retrieve chunks |
| `IngestVideoUseCase` | Orchestrates pipeline steps | Does not implement any step itself |

**Violation to avoid:** A `VideoProcessor` class that extracts audio, transcribes, extracts frames, runs OCR, embeds, and upserts. That is a God class — impossible to test, impossible to extend.

### Open/Closed Principle (OCP)
*Open for extension, closed for modification.*

The `ModelRegistry` in `app/embeddings/registry.py` is the canonical example:
- **Open for extension:** Adding `nomic-embed-text` requires creating a new class implementing `IEmbeddingModel` and calling `ModelRegistry.register("nomic-embed-text", NomicModel)`.
- **Closed for modification:** `EmbeddingService`, `IngestVideoUseCase`, and all callers are unchanged.

Similarly, adding a new OCR engine (e.g., Tesseract) only requires a new Adapter class. `OCRService` never changes.

### Liskov Substitution Principle (LSP)
*Subclasses must be substitutable for their base class without breaking callers.*

All OCR engine adapters implement:
```python
def extract(self, image: np.ndarray) -> list[TextBlock]
```

`OCRService` calls `self.engine.extract(image)`. It doesn't care if the engine is PaddleOCR or EasyOCR. The return type is always `List[TextBlock]`. Substituting one for the other breaks nothing.

### Interface Segregation Principle (ISP)
*Don't force a class to implement methods it doesn't use.*

Retrieval interfaces are split:
- `IDenseRetriever` — has only `search(query_vector, video_id, top_k)`.
- `ISparseRetriever` — has only `search(query, video_id, top_k)`.
- `IHybridRetriever` — has `search(query, query_vector, video_id, top_k, alpha)`.

If we had one `IRetriever` interface with all three method signatures, a pure dense retriever would be forced to implement sparse methods it doesn't need. ISP says: keep interfaces small and focused.

### Dependency Inversion Principle (DIP)
*High-level modules depend on abstractions, not concretions.*

```
IngestVideoUseCase
    depends on → IVideoRepository  (not VideoRepository)
    depends on → IEmbeddingModel   (not BGEModel)
    depends on → IOCREngine        (not PaddleOCR)
```

In tests, we inject mock implementations of these interfaces. The use case is tested in pure Python with no database, no GPU, no OCR library installed.

---

## Part 3: Design Patterns — Where and Why

### Strategy Pattern
**Where:** `OCRService` (engine selection), `LLMService` (backend selection)  
**Why:** Swap implementations at runtime based on config without changing callers.  
**How it works:** The service holds a reference to an interface (e.g., `IOCREngine`). The concrete implementation (PaddleOCR vs EasyOCR) is injected from outside. The service method calls `self.engine.extract(image)` — it never `isinstance()` checks.

### Factory Pattern
**Where:** `ModelRegistry.get_model(name)`, `embeddings/registry.py`  
**Why:** Model loading is complex (download weights, set device, configure tokenizer). The factory hides all of this behind a single name-to-instance lookup. Callers say `registry.get_model("BAAI/bge-small-en-v1.5")` and receive a ready model.

### Repository Pattern
**Where:** `VideoRepository`, `TranscriptRepository`, `VectorRepository`  
**Why:** Business logic never writes SQL. If we switch from PostgreSQL to a different database, only the repository classes change. Use cases are database-agnostic.

### Adapter Pattern
**Where:** `PaddleOCRAdapter`, `EasyOCRAdapter` (implemented in Phase 5)  
**Why:** PaddleOCR returns nested lists of bounding box coordinates and text. EasyOCR returns tuples in a different format. Neither matches our internal `TextBlock` entity. Adapters translate each external API into our unified contract.

### Builder Pattern
**Where:** `PromptBuilder` in `app/generation/prompt_builder.py`  
**Why:** A RAG prompt has many optional components: system instruction, retrieved context, timestamp annotations, user query, output format instructions. A builder lets us chain only the components we need and produces a validated prompt. Avoids a 7-argument prompt construction function.

### Singleton Pattern
**Where:** `ModelRegistry` (via `get_instance()`), Settings (via `@lru_cache`)  
**Why:** Loading a 384-dim sentence-transformer model takes ~200ms and ~200MB RAM. A Singleton ensures it happens once per process. All requests share the loaded model without reloading.

### Observer Pattern
**Where:** `PipelineEvent` entity, pipeline event hooks  
**Why:** We want to log timing, alert on slowdowns, and emit metrics for each pipeline stage. But `WhisperService` should not contain logging calls, timing logic, AND transcription logic (SRP violation). Instead, services emit `PipelineEvent` objects to an event bus. Observers (logger, metrics collector) react to events independently.

---

## Part 4: Multi-Modal RAG Pipeline — How It All Connects at Query Time

This is the most important concept to understand for an AI Engineer interview.

### What is RAG?

Retrieval-Augmented Generation (RAG) = retrieve relevant context from a database → give it to an LLM → get a grounded answer. Without retrieval, the LLM hallucinates. Without generation, you get search results, not answers.

### The Three Parallel Ingestion Pipelines

At ingestion time, three pipelines run simultaneously (or sequentially) and produce chunks stored in Qdrant:

```
Video File
    │
    ├─── Pipeline A: Audio
    │       FFmpeg extracts WAV → Whisper transcribes → 
    │       Chunks split at ~512 tokens with 50-token overlap →
    │       Each chunk: { text, start_time, end_time, language }
    │
    ├─── Pipeline B: Vision (Frames)
    │       OpenCV samples 1 frame/sec → PaddleOCR runs on each frame →
    │       Each frame: { OCR_text, timestamp, scene_label, description }
    │
    └─── Pipeline C: Objects (Frames)
            YOLO detects objects in each frame →
            Each frame: { object_labels, timestamp }
```

All output from all three pipelines is:
1. **Embedded** into dense vectors by `EmbeddingService` (using bge-small)
2. **Stored** in Qdrant with a `payload` containing: `video_id`, `timestamp`, `modality`, `text`

### At Query Time: The Full RAG Flow

```
User Question: "When did the instructor explain transformers?"
        │
        ▼
1. EmbeddingService.encode(question) → query_vector [0.23, -0.11, ...]
        │
        ▼
2. HybridRetriever.search(question, query_vector, video_id)
        │
        ├── DenseRetriever: Qdrant ANN search on query_vector
        │   Filter: payload.video_id == "abc-123"
        │   Returns 10 candidates with cosine similarity scores
        │
        └── BM25SparseRetriever: keyword search on "transformers"
            Returns 10 candidates with BM25 scores
            │
            ▼
        Reciprocal Rank Fusion merges both lists → 15 unique candidates
        │
        ▼
3. CrossEncoderReranker.rerank(question, candidates, top_k=5)
        Cross-encoder jointly encodes (question, each_chunk) → relevance score
        Returns top 5 most relevant chunks
        │
        ▼
4. ContextBuilder.build(top_5_chunks)
        [00:04:12 - AUDIO] "The instructor begins by introducing the 
         attention mechanism as the core of transformer architecture..."
        [00:04:45 - VISUAL] OCR from whiteboard: "Q, K, V = Attention(Q,K,V)"
        [00:05:03 - AUDIO] "Self-attention allows every token to attend..."
        │
        ▼
5. PromptBuilder
        .set_system_instruction("You are a helpful video analyst...")
        .add_context_chunks(top_5_chunks)
        .set_user_query("When did the instructor explain transformers?")
        .build()
        │
        ▼
6. LLMService.generate(prompt) via Ollama (Qwen3 local)
        │
        ▼
Answer: "The instructor began explaining transformers at 4:12, starting 
         with the attention mechanism. The core equation (Q, K, V) appeared 
         on the whiteboard at 4:45. The explanation continued until 5:30."
```

### Why This Architecture Enables Grounded Temporal Answers

Every chunk stored in Qdrant carries a `timestamp` in its payload. When the retriever finds a relevant chunk, the timestamp travels with it. The ContextBuilder annotates each context block with `[MM:SS - MODALITY]`. The LLM then reads this structured context and can generate temporally precise answers.

**This is why the three pipelines must produce timestamped chunks.** Without timestamps, you get "transformers were discussed" — not "at 4:12."

### Why Hybrid Retrieval Beats Dense-Only

Dense search works for semantic similarity ("explain transformers" → finds chunks about attention mechanisms). But it fails for exact terms: "What was on the whiteboard at 4:32?" — a purely semantic search for "4:32" finds nothing useful. BM25 sparse search excels at keyword matching (timestamps, proper nouns, code identifiers). Hybrid fusion gets the best of both.

---

## Part 5: Interview Preparation

**If a hiring manager asks: "Walk me through your VideoMind AI architecture,"**

> "I built a production-grade multi-modal RAG system using Clean Architecture. The core insight is the Dependency Rule — inner layers never import outer layers. My domain entities and interfaces define contracts. My service layer runs the ML pipelines — Whisper for transcription, PaddleOCR for OCR, bge-small for embeddings. My repository layer abstracts PostgreSQL and Qdrant. My use cases orchestrate the pipeline without knowing about HTTP or databases. My FastAPI routes just parse input, call a use case, and return output.

> At query time, a user question is embedded, retrieved via hybrid dense+BM25 search against Qdrant, reranked by a cross-encoder, and the top chunks — with their timestamps — are assembled into a structured context. That context goes to a locally-running LLM via Ollama, which generates a grounded, timestamp-cited answer.

> The system runs 100% locally with one `docker-compose up`. I chose this architecture because every component is independently testable, every dependency is mockable, and every ML model can be swapped without changing callers."
