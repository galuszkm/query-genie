# Stage 1: Install Python dependencies with uv (builder)
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS python-builder

WORKDIR /app

COPY pyproject.toml ./pyproject.toml
RUN uv sync --no-cache --group agent-service

# Stage 2: Runtime (uv base for minimal image)
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

# Copy virtual environment from python builder
COPY --from=python-builder /app/.venv /app/.venv

# Copy agent service source
COPY agent_service/src/ ./src/

# Create sessions directory
RUN mkdir -p strands_sessions

ENV PATH="/app/.venv/bin:$PATH"

CMD ["python", "-m", "src.main"]
