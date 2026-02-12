# Multi-stage build for Jenkins MCP Server

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

# Development stage
FROM base as development

# Install development dependencies
RUN pip install --no-cache-dir debugpy pytest pytest-cov black isort flake8

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash jenkins-mcp && \
    chown -R jenkins-mcp:jenkins-mcp /app

# Copy application code
COPY --chown=jenkins-mcp:jenkins-mcp . .

# Switch to non-root user
USER jenkins-mcp

# Expose MCP server port and debug port
EXPOSE 8000 5678

# Default command for development (can be overridden)
CMD ["python", "-m", "jenkins_mcp_server.main"]

# Production stage
FROM base as production

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash jenkins-mcp && \
    chown -R jenkins-mcp:jenkins-mcp /app

# Copy application code
COPY --chown=jenkins-mcp:jenkins-mcp . .

# Switch to non-root user
USER jenkins-mcp

# Expose MCP server port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set default command
CMD ["python", "-m", "jenkins_mcp_server.main"]

# Default stage (production)
FROM production as default