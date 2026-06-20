# =============================================================================
# VideoMind AI — Frontend Dockerfile
# =============================================================================

FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY frontend/requirements.txt .
RUN pip install --default-timeout=1000 --no-cache-dir --upgrade pip \
    && pip install --default-timeout=1000 --no-cache-dir -r requirements.txt

# Copy frontend source
COPY frontend/ ./frontend/

# Set Python unbuffered and don't write bytecode
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Entrypoint
CMD ["streamlit", "run", "frontend/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
