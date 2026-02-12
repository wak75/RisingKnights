# Multi-stage build for Kubernetes MCP Server

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
RUN useradd --create-home --shell /bin/bash k8s-mcp && \
    chown -R k8s-mcp:k8s-mcp /app

# Switch to non-root user
USER k8s-mcp

# Expose MCP server port
EXPOSE 8001

# Environment variables (can be overridden)
ENV K8S_MCP_HOST=0.0.0.0 \
    K8S_MCP_PORT=8001 \
    K8S_MCP_TRANSPORT=sse

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8001/sse 2>/dev/null || exit 1

# Set default command
CMD ["python", "-m", "kubernetes_mcp_server.main"]

# Default stage (production)
FROM production as default