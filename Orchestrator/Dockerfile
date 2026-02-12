# Multi-stage build for Orchestrator Agent

# Base stage with common dependencies
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create application directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./
COPY README.md ./

# Copy source code
COPY src/ ./src/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Production stage
FROM base as production

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash orchestrator && \
    chown -R orchestrator:orchestrator /app

# Create sessions directory for persistence
RUN mkdir -p /app/sessions && chown orchestrator:orchestrator /app/sessions

# Switch to non-root user
USER orchestrator

# Expose Orchestrator port
EXPOSE 8080

# Environment variables (can be overridden)
ENV ORCHESTRATOR_HOST=0.0.0.0 \
    ORCHESTRATOR_PORT=8080 \
    ORCHESTRATOR_MODEL=gemini-2.0-flash

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Set default command - run the web server
CMD ["python", "-c", "from orchestrator.main import run_server; run_server()"]

# Default stage (production)
FROM production as default