# Stage 1: Build frontend
FROM node:lts-alpine AS frontend-builder

WORKDIR /frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm i

# Copy frontend source
COPY frontend/ ./

# Build frontend
RUN npm run build

# Stage 2: Install Python dependencies with uv (builder)
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS python-builder

WORKDIR /app

COPY pyproject.toml ./pyproject.toml
RUN uv sync --no-cache --group backend

# Stage 3: Runtime (uv base for minimal image)
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

# Copy virtual environment from python builder
COPY --from=python-builder /app/.venv /app/.venv

# Copy backend source
COPY backend/src/ ./src/

# Copy built frontend static files from frontend builder
COPY --from=frontend-builder /frontend/dist ./src/static

# Create sessions directory
RUN mkdir -p strands_sessions

EXPOSE 8080

ENV PATH="/app/.venv/bin:$PATH"
ENV WORKERS=4

CMD uvicorn src.app:app --host 0.0.0.0 --port 8080 --workers ${WORKERS}
