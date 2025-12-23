"""FastAPI application factory.

Backend API service that handles HTTP requests and communicates with
the agent service via Redis queue and Pub/Sub.
"""

import logging
from collections.abc import AsyncGenerator, MutableMapping
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi.errors import RateLimitExceeded

from .api.dependencies import set_redis_client
from .api.middleware import (
    ErrorTrackingMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)
from .api.rate_limit import limiter, rate_limit_exceeded_handler
from .api.routes import router
from .config import settings
from .logging_config import configure_logging
from .utils.redis_client import RedisClient

logger = logging.getLogger(__name__)

# Jinja2 templates directory
TEMPLATES = Jinja2Templates(directory=Path(__file__).resolve().parent / "templates")


class CachedStaticFiles(StaticFiles):
    """StaticFiles with cache headers."""

    async def get_response(
        self, path: str, scope: MutableMapping[str, Any]
    ) -> Response:
        """Get response with cache headers.

        Args:
            path: Static file path
            scope: ASGI scope

        Returns:
            Response with cache headers
        """
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "public, max-age=3600"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Application lifespan handler.

    Initializes Redis client for communication with agent service.
    """
    redis_client = None

    # Initialize Redis client for service communication
    logger.info("Connecting to Redis...")
    try:
        redis_client = RedisClient()
        await redis_client.connect()
        set_redis_client(app.state, redis_client)
        logger.info("Redis client connected")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        set_redis_client(app.state, None)
        raise RuntimeError(
            "Redis connection required for agent service communication"
        ) from e

    yield

    # Cleanup
    logger.info("Shutting down services...")
    if redis_client:
        await redis_client.disconnect()
        set_redis_client(app.state, None)
        logger.info("Redis client disconnected")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    # Configure structured logging
    configure_logging(level="INFO")

    app = FastAPI(
        title="AI Chat API",
        description="Streaming AI chat with PostgreSQL MCP server",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Add exception handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle request validation errors."""
        logger.warning(f"Validation error: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "detail": exc.errors(),
                "body": exc.body,
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        equest: Request, exc: HTTPException
    ) -> JSONResponse:
        """Handle HTTP exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle all other exceptions."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error",
                "error": str(exc) if logger.level <= logging.DEBUG else None,
            },
        )

    # Add custom middleware (order matters - first added is outermost)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(ErrorTrackingMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    # Configure slowapi rate limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_allowed_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    # Mount static directory
    static_dir = Path(__file__).parent / "static"
    if not static_dir.exists():
        static_dir.mkdir(parents=True, exist_ok=True)
    app.mount(
        "/ai/static",
        CachedStaticFiles(directory=str(static_dir.resolve())),
        name="static",
    )

    # Main index routes
    @app.get("/")
    @app.get("/ai")
    async def index(request: Request) -> Response:
        """Serve the main application page."""
        return TEMPLATES.TemplateResponse(
            "index.html",
            {
                "request": request,
                "static": "/ai/static",
            },
        )

    return app


app = create_app()
