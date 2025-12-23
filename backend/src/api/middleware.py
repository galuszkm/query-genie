"""Middleware for request logging and error tracking."""

import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..logging_config import clear_request_context, get_logger, set_request_context

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging all HTTP requests with correlation IDs."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request with logging.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response from handler
        """
        # Generate or extract request ID
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        session_id = request.headers.get("x-session-id")

        # Set context for structured logging
        set_request_context(request_id=request_id, session_id=session_id)

        # Log request
        logger.info(
            f"{request.method} {request.url.path} - Started",
        )

        start_time = time.time()

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Log response
            logger.info(
                f"{request.method} {request.url.path} - "
                f"Status: {response.status_code} - "
                f"Duration: {duration:.3f}s"
            )

            # Add correlation headers to response
            response.headers["X-Request-ID"] = request_id
            if session_id:
                response.headers["X-Session-ID"] = session_id

            return response

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"{request.method} {request.url.path} - "
                f"Error: {str(e)} - "
                f"Duration: {duration:.3f}s",
                exc_info=True,
            )
            raise
        finally:
            clear_request_context()


class ErrorTrackingMiddleware(BaseHTTPMiddleware):
    """Middleware for catching and logging unhandled exceptions."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request with error tracking.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response from handler or error response
        """
        try:
            return await call_next(request)
        except Exception as e:
            logger.error(
                f"Unhandled exception in {request.method} {request.url.path}: {e}",
                exc_info=True,
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "error_type": type(e).__name__,
                },
            )

            # Return generic error response
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "error": str(e)
                    if logger.level <= 10
                    else "An error occurred",  # Show details in DEBUG
                },
            )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers to all responses."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Add security headers to response.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response with security headers
        """
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        return response
