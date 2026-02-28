# ============================================================
# Stage 1: Builder
# Install hash-verified dependencies and pre-warm ONNX model
# ============================================================
FROM python:3.11-slim@sha256:fba6f3b73795df99960f4269b297420bdbe01a8631fc31ea3f121f2486d332d0 AS builder

WORKDIR /build

# Install pinned build tools
RUN pip install --no-cache-dir setuptools==75.8.2 wheel==0.45.1

# Copy package manifest first (layer caching: only re-installs if deps change)
COPY pyproject.toml .
COPY src/ src/

# Create venv and install the package with all dependencies
RUN python -m venv /build/venv && \
    /build/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /build/venv/bin/pip install --no-cache-dir .

# Pre-warm the ChromaDB ONNX embedding model (~79MB)
# Downloads all-MiniLM-L6-v2 to ~/.cache/chroma/ at build time
# so containers don't have a 30-60s cold-start delay on first request
RUN /build/venv/bin/python -c \
    "from chromadb.utils.embedding_functions import DefaultEmbeddingFunction; DefaultEmbeddingFunction()()"


# ============================================================
# Stage 2: Runtime
# Slim image with only what's needed to run the app
# ============================================================
FROM python:3.11-slim@sha256:fba6f3b73795df99960f4269b297420bdbe01a8631fc31ea3f121f2486d332d0 AS runtime

WORKDIR /app

# Prevent .pyc files and ensure real-time log output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create non-root user with no login shell
RUN groupadd -r appuser && \
    useradd --no-log-init -r -g appuser -m -s /bin/false appuser

# Copy installed venv from builder with explicit ownership
COPY --chown=appuser:appuser --from=builder /build/venv /app/venv

# Copy pre-warmed ONNX model cache with correct ownership
COPY --chown=appuser:appuser --from=builder /root/.cache/chroma /home/appuser/.cache/chroma

# Copy application code
COPY --chown=appuser:appuser apps/ apps/
COPY --chown=appuser:appuser src/ src/
COPY --chown=appuser:appuser pyproject.toml .

# Copy static data (questions + exemplars are shipped with the image)
COPY --chown=appuser:appuser data/questions/ data/questions/
COPY --chown=appuser:appuser data/exemplars/ data/exemplars/

# Create writable directories for runtime-generated data
RUN mkdir -p data/chroma data/personas && \
    chown appuser:appuser data/chroma data/personas

# Streamlit configuration via environment variables
ENV STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    PATH="/app/venv/bin:$PATH" \
    HOME=/home/appuser

# Switch to non-root user
USER appuser

# Expose Streamlit default port
EXPOSE 8501

# Python-based health check (avoids installing curl and expanding attack surface)
# --start-period allows Streamlit time to boot before counting failures
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')"

# Run the Streamlit app
ENTRYPOINT ["streamlit", "run", "apps/streamlit_app.py"]
