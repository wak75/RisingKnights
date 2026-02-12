# GitHub MCP Server with SSE Transport Wrapper
# Uses official GitHub MCP with stdio and wraps it with SSE proxy

FROM python:3.11-slim AS base

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages for SSE wrapper
RUN pip install --no-cache-dir \
    fastmcp>=2.0.0 \
    httpx \
    uvicorn

# Copy the wrapper script
COPY wrapper.py ./

# Create non-root user
RUN useradd --create-home --shell /bin/bash github-mcp && \
    chown -R github-mcp:github-mcp /app

USER github-mcp

# Default port
EXPOSE 8002

# Run the SSE wrapper
CMD ["python", "wrapper.py"]