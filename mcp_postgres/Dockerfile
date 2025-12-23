# Build from project root: docker build -f mcp_postgres/Dockerfile .

# Stage 1: Install Python dependencies with uv (builder)
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS python-builder

WORKDIR /app

COPY pyproject.toml ./pyproject.toml
RUN uv sync --no-cache --group mcp-server

# Stage 2: Runtime (uv base for minimal image)
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

# Copy virtual environment from python builder
COPY --from=python-builder /app/.venv /app/.venv

# Copy MCP server source code
COPY mcp_postgres/src/ ./src/

# Set python path to include app root and venv bin
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app

EXPOSE 8000

# Run the server module
CMD ["python", "-m", "src.server"]
