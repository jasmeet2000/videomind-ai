# 🎬 VideoMind AI

**VideoMind AI** is a multi-modal video intelligence platform that allows you to query, search, and chat with your video files using natural language. 

By combining cutting-edge speech transcription, optical character recognition (OCR), scene analysis, and Large Language Models (LLMs), VideoMind AI completely unlocks the contents of your videos, making them fully searchable and interactive.

## ✨ Features

- **🗣️ Automatic Speech Recognition (ASR)**: Transcribes video audio accurately using OpenAI's Whisper models.
- **👁️ Computer Vision & OCR**: Extracts frames, detects objects, identifies scenes, and reads on-screen text using PaddleOCR/EasyOCR and OpenCV.
- **🔍 Semantic Video Search**: Uses a Hybrid Search pipeline (BM25 Sparse + Dense Vector embeddings) backed by **Qdrant** and re-ranked using a Cross-Encoder to find the exact moment your query appears.
- **💬 Chat with Video (RAG)**: Ask contextual questions about your video. VideoMind AI retrieves the most relevant chunks (audio, visual, or text) and synthesizes an answer using a local LLM via **Ollama**.
- **🎨 Beautiful UI**: A highly responsive, glassmorphic Streamlit frontend tailored for easy uploads and interactive chat.
- **🐳 Fully Dockerized**: Spin up the entire stack locally with a single command. 100% data privacy with local processing—no paid APIs required.

## 🏗️ Architecture

VideoMind AI is built following Clean Architecture principles:
- **Frontend**: Streamlit (Python)
- **Backend**: FastAPI (Python 3.11)
- **Vector Database**: Qdrant (for dense embeddings)
- **Metadata Database**: PostgreSQL (for tracking videos and chunk locations)
- **LLM Engine**: Ollama (Running `qwen` or `llama` models locally)

## 🚀 Getting Started

### Prerequisites
- Docker and Docker Compose
- (Optional but recommended) NVIDIA GPU with container toolkit enabled for faster processing.

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/videomind-ai.git
   cd videomind-ai
   ```

2. **Environment Setup:**
   Copy the example environment file and adjust any variables if necessary (e.g., changing the default `OLLAMA_MODEL`):
   ```bash
   cp .env.example .env
   ```

3. **Start the stack with Docker Compose:**
   ```bash
   docker-compose up --build
   ```
   This command will spin up the FastAPI backend, Streamlit frontend, Postgres, Qdrant, and Ollama containers.

4. **Pull the LLM Model (One-time setup):**
   Open a new terminal and tell your local Ollama container to pull the default model (`llama3:latest`):
   ```bash
   docker exec -it videomind_ollama ollama run llama3:latest
   ```
   *(Note: If you changed the model in your `.env` file to something else like `qwen2.5-coder:7b`, pull that model instead).*

---

## 🌐 Services & Ports

Once `docker-compose up --build` completes, all services will be available on your local machine:

| Service | URL | Description |
|---|---|---|
| 🎨 **Streamlit UI** | http://localhost:8501 | Main user interface — upload videos and chat |
| ⚡ **FastAPI Backend** | http://localhost:8000 | REST API server |
| 📖 **API Docs (Swagger)** | http://localhost:8000/docs | Interactive API documentation |
| 📖 **API Docs (ReDoc)** | http://localhost:8000/redoc | Alternative API docs viewer |
| 🔍 **Qdrant Dashboard** | http://localhost:6333/dashboard | Vector database admin panel |
| 🤖 **Ollama API** | http://localhost:11434 | Local LLM inference endpoint |
| 🐘 **PostgreSQL** | localhost:5432 | Metadata database (user: `videomind`, pass: `videomind`, db: `videomind`) |

---

### Usage

1. Open your browser and navigate to **http://localhost:8501**.
2. **Upload a video** via the sidebar widget.
3. Wait for the processing pipeline to complete (Audio extraction → Transcription → Frame extraction → OCR → Embedding ingestion).
4. Use the **Chat** tab to ask questions (e.g., "What was the main topic discussed?" or "Summarize the whiteboard text").
5. Use the **Search** tab to find specific timestamps based on keywords or semantic meaning.

## 🧪 Testing

VideoMind AI maintains strict code quality and >80% test coverage.

To run tests locally:
```bash
# Setup a virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov httpx asgi-lifespan

# Run tests with coverage
pytest --cov=app
```

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
