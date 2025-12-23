# Backend API Service

## Overview

The Backend API Service is a FastAPI-based HTTP gateway that handles client requests and coordinates with the Agent Service via Redis. It provides SSE (Server-Sent Events) streaming for real-time AI responses, manages authentication and rate limiting, and serves static frontend assets.

The service acts as a thin API layer, enqueuing tasks to Redis for processing by the Agent Service and forwarding streaming events back to clients. This architecture decouples HTTP handling from AI agent operations, enabling independent scaling and preventing long-running LLM calls from blocking web server threads.

## System Architecture

```
        ┌──────────────────────────────────────────────────────────────────────────────────┐
        │                                 FRONTEND CLIENT                                  │
        │                            (React + SSE EventSource)                             │
        └──────────────────────────────────────────────────────────────────────────────────┘
                                               │
                                               ▼ HTTP/SSE
        ┌──────────────────────────────────────────────────────────────────────────────────┐
        │                              BACKEND API SERVICE                                 │
        │  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────────────┐  │
        │  │   FastAPI App   │───>│   Redis Client   │───>│      Task Queue (LPUSH)     │  │
        │  │  (HTTP + SSE)   │    │   (Enqueue)      │    │      Pub/Sub (Subscribe)    │  │
        │  └─────────────────┘    └──────────────────┘    └─────────────────────────────┘  │
        │           │                                                                      │
        │           ▼                                                                      │
        │  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────────────┐  │
        │  │   Middleware    │    │   Rate Limiter   │    │    Security Headers         │  │
        │  │ (Auth, Logging) │    │   (SlowAPI)      │    │    (CSP, XSS Protection)    │  │
        │  └─────────────────┘    └──────────────────┘    └─────────────────────────────┘  │
        └──────────────────────────────────────────────────────────────────────────────────┘
                                               │
                                               ▼ Redis
        ┌──────────────────────────────────────────────────────────────────────────────────┐
        │                                     REDIS                                        │
        │                    (Task Queue: agent:tasks | Pub/Sub: task:{id})                │
        └──────────────────────────────────────────────────────────────────────────────────┘
                                               │
                                               ▼
        ┌──────────────────────────────────────────────────────────────────────────────────┐
        │                               AGENT SERVICE                                      │
        │                     (Processes tasks, publishes SSE events)                      │
        └──────────────────────────────────────────────────────────────────────────────────┘
```

## Key Features

| Feature | Description |
|---------|-------------|
| **Real-time Streaming** | SSE-based streaming delivers events from Agent Service as they happen, providing responsive UX with live progress indicators |
| **Redis Queue Integration** | Task enqueuing to Redis LIST and event consumption from Pub/Sub channels |
| **Enterprise Security** | Secure httpOnly cookies, API key authentication, CORS controls, request correlation IDs, rate limiting, and security headers |
| **Static Asset Serving** | Serves frontend build with cache headers |
| **Health Monitoring** | Health check endpoints for Redis connectivity |

## Benefits & Advantages

**For End Users:**
- Query databases using natural language without SQL knowledge
- Receive AI-summarized insights instead of raw data tables
- Track agent reasoning process in real-time through workflow visualization

**For Developers:**
- Simple API gateway pattern - easy to understand and extend
- Decoupled architecture enables independent scaling
- Comprehensive logging with request/session correlation
- Type-safe Pydantic models throughout the codebase

**For Operations:**
- Stateless API servers scale horizontally
- Health check endpoints for monitoring and load balancers
- Graceful shutdown with resource cleanup
- Configurable rate limits

## Core Components

| Component | Purpose |
|-----------|---------|
| `app.py` | FastAPI application factory with lifespan management and middleware registration |
| `config.py` | Centralized environment configuration for API, Redis, and security policies |
| `logging_config.py` | Structured logging with correlation IDs and context propagation |
| `api/routes.py` | HTTP endpoints for chat streaming and health checks |
| `api/middleware.py` | Request logging, error tracking middleware |
| `api/security.py` | Security headers middleware (CSP, XSS protection) |
| `api/rate_limit.py` | SlowAPI rate limiting configuration |
| `utils/redis_client.py` | Redis task queue and Pub/Sub operations |

---

## Module Reference

### Application Entry (`app.py`)

The application factory creates and configures the FastAPI application with production-ready defaults. It manages the application lifespan, initializing the agent service at startup and ensuring graceful shutdown with proper resource cleanup.

**Key Responsibilities:**
- Register middleware stack (error tracking, request logging, CORS, security headers)
- Mount static file serving with cache headers
- Initialize Redis client via async lifespan context manager
- Include API routes with proper prefixing

```
Application Startup Flow:
────────────────────────
1. configure_logging() → Set up structured logging
2. Create FastAPI app with lifespan handler
3. Add middleware: SecurityHeaders → ErrorTracking → RequestLogging → CORS
4. Include router at /ai/api prefix
5. Mount static files at /ai/static
6. Lifespan: RedisClient() → connect() → yield → disconnect()
```

---

### Configuration (`config.py`)

Centralized configuration management using environment variables with sensible defaults and validation.

| Category | Variables | Description |
|----------|-----------|-------------|
| **Security** | `API_KEY`, `ALLOWED_ORIGINS` | Authentication and CORS configuration |
| **Environment** | `ENVIRONMENT` | development/production/staging |
| **Redis** | `REDIS_URL`, `REDIS_TASK_QUEUE` | Redis connection and queue name |

---

### Logging (`logging_config.py`)

Production logging infrastructure with request correlation, session tracking, and structured output format. Uses Python's `contextvars` for thread-safe context propagation across async boundaries.

**Features:**
- `ContextFilter` injects `request_id` and `session_id` into all log records
- `StructuredFormatter` produces consistent, parseable log lines
- Third-party library noise (httpx, asyncio) suppressed to WARNING level
- Context helpers for middleware integration

**Log Format:**
```
[INFO] [src.api.routes] [req:a1b2c3d4] [sess:e5f6g7h8] POST /ai/api/chat/stream - Started
```

---

### API Module (`api/`)

RESTful API layer providing HTTP endpoints for chat streaming and health monitoring.

#### Routes (`routes.py`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ai/api/health` | GET | Health check with Redis status |
| `/ai/api/chat/stream` | POST | SSE streaming chat endpoint (via Redis) |

**Streaming Flow:**
```
User Request
    │
    ▼
POST /ai/api/chat/stream
    │
    ├──▶ enqueue_task() → Redis LIST (agent:tasks)
    │
    ├──▶ subscribe_task_events() → Redis Pub/Sub (task:{id})
    │
    ▼
Yield SSE events as they arrive from Agent Service
    │
    ├──▶ {"type": "session", "session_id": ...}
    ├──▶ {"type": "token", "content": ...}
    ├──▶ {"type": "tool", "name": ..., ...}
    │
    ▼
    └──▶ {"type": "complete", "response": ..., "workflow": [...]}
```

**Streaming Response Events:**
```json
{"type": "session", "session_id": "uuid"}
{"type": "token", "content": "Hello"}
{"type": "tool", "name": "query", "message": "🔎 Running query..."}
{"type": "complete", "response": "...", "workflow": [...]}
```

#### Models (`models.py`)

Pydantic request/response models ensuring type safety:

- `ChatRequest`: message, stream flag (session via cookie)
- `ChatResponse`: response text, session_id
- `HealthResponse`: status, agent_initialized, mcp_status

**Session Management**: Session IDs are managed via secure httpOnly cookies:
- `HttpOnly` flag prevents JavaScript access (XSS protection)
- `Secure` flag enforces HTTPS in production
- `SameSite=Strict` prevents CSRF attacks
- `Max-Age=7200` (2 hours) matches backend session TTL

#### Dependencies (`dependencies.py`)

Dependency injection for:
- Redis client instance (singleton pattern via lifespan)
- Optional API key authentication guard

#### Middleware (`middleware.py`)

| Middleware | Purpose |
|------------|---------|
| `RequestLoggingMiddleware` | Log all requests with timing and correlation IDs |
| `ErrorTrackingMiddleware` | Catch unhandled exceptions, return structured errors |

#### Security (`security.py`)

`SecurityHeadersMiddleware` adds security headers to all responses:
- Content-Security-Policy
- X-Content-Type-Options
- X-Frame-Options
- X-XSS-Protection

---

### Utils Module (`utils/`)

Redis client utilities for task queue and event streaming.

#### Redis Client (`redis_client.py`)

| Function | Purpose |
|----------|---------|
| `RedisClient` | Connection wrapper with connect/disconnect lifecycle |
| `enqueue_task()` | Push task to Redis LIST (agent:tasks) |
| `subscribe_task_events()` | Subscribe to Pub/Sub channel for SSE events |
| `create_error_event()` | Create error event dictionary |

---

## Environment Configuration

Create a `.env` file based on `example.env`:

```bash
# Required: Redis
REDIS_URL=redis://localhost:6379/0
REDIS_TASK_QUEUE=agent:tasks

# Optional: Security
API_KEY=your-secret-key
ALLOWED_ORIGINS=http://localhost:5173

# Optional: Environment
ENVIRONMENT=development  # or production
```

---

## Usage

### Building the Frontend

The backend serves the compiled frontend static assets from `src/static/`.

**For Local Development:**
```bash
cd frontend
npm run build:backend  # Builds directly into ../backend/src/static
```

**For Docker/Production:**
Frontend is automatically built during the Docker container build process using a multi-stage build. No manual build step needed - just run:
```bash
docker compose up --build app
```

The Dockerfile handles:
1. Building frontend assets using Node.js
2. Copying built files into the backend container
3. Serving them from the FastAPI app

### Running the Server

```bash
# Development (requires Redis and Agent Service running)
uvicorn backend.src.app:create_app --factory --reload --port 8080

# Production (with Docker)
docker compose up app
```

### API Examples

**Streaming Chat Request:**
```bash
# Session is managed automatically via secure httpOnly cookies
curl -X POST http://localhost:8080/ai/api/chat/stream \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"message": "How many users are in the system?"}'
```

**Health Check:**
```bash
curl http://localhost:8080/ai/api/health
# {"status": "healthy", "redis_status": "ok"}
```

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Web Framework | FastAPI 0.125 |
| Async HTTP | sse-starlette |
| Rate Limiting | SlowAPI |
| Message Broker | Redis (redis-py) |
| Validation | Pydantic 2.x |
| Logging | Python logging with structured formatter |
