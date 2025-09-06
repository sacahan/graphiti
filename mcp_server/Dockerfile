# syntax=docker/dockerfile:1.9
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv using the installer script
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Add uv to PATH
ENV PATH="/root/.local/bin:${PATH}"

# Configure uv for optimal Docker usage
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    MCP_SERVER_HOST="0.0.0.0" \
    PYTHONUNBUFFERED=1

# Create non-root user
RUN groupadd -r app && useradd -r -d /app -g app app

# Copy the graphiti-core source code and build a wheel
COPY graphiti_core/ /tmp/graphiti-core/graphiti_core/
COPY pyproject.toml README.md LICENSE /tmp/graphiti-core/
WORKDIR /tmp/graphiti-core
RUN uv build --wheel

# Switch back to app directory
WORKDIR /app

# Copy MCP server project files for dependency installation
COPY mcp_server/pyproject.toml ./

# Remove the editable dependency and use the wheel instead
RUN sed -i 's/graphiti-core = { path = "[^"]*", editable = true }//' pyproject.toml

# Install the graphiti-core wheel and other dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv venv && \
    uv pip install /tmp/graphiti-core/dist/*.whl && \
    uv pip install -e .

# Copy application code
COPY mcp_server/graphiti_mcp_server.py ./

# Change ownership to app user
RUN chown -Rv app:app /app

# Switch to non-root user
USER app

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["uv", "run", "graphiti_mcp_server.py"]
