# syntax=docker/dockerfile:1

# Build stage
FROM python:3.12-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files first (for layer caching)
COPY pyproject.toml ./
COPY uv.lock* ./
COPY README.md ./

# Copy source for editable install
COPY src/ ./src/

# Install dependencies (creates lock if needed)
RUN uv sync --no-dev

# Runtime stage
FROM python:3.12-slim AS runtime

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash kgpt

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY src/ ./src/

# Create data directory
RUN mkdir -p /app/data && chown -R kgpt:kgpt /app

# Switch to non-root user
USER kgpt

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"
ENV DATA_DIR=/app/data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run the application
CMD ["uvicorn", "kgpt.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
