"""Rate limiting for API endpoints using slowapi.

This module provides rate limiting functionality using the slowapi library,
which offers better reliability and features compared to custom implementations.
For single-worker deployments, in-memory storage is sufficient and avoids
the complexity of Redis setup.
"""

from fastapi import Request, Response
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.status import HTTP_429_TOO_MANY_REQUESTS


def get_client_identifier(request: Request) -> str:
    """Get unique client identifier from request.

    Uses IP address combined with API key (if present) to identify clients.
    This allows for more granular rate limiting when API keys are used.

    Args:
        request: FastAPI request object

    Returns:
        Unique client identifier string
    """
    client_ip = get_remote_address(request)
    api_key = request.headers.get("x-api-key", "")
    # Include API key in identifier if present, otherwise just use IP
    return f"{client_ip}:{api_key}" if api_key else client_ip


# Initialize slowapi limiter with in-memory storage
# For single-worker deployments, in-memory storage is sufficient
# Default limits: 60 requests/minute, max 10 burst/second
limiter = Limiter(
    key_func=get_client_identifier,
    default_limits=["60/minute", "10/second"],
    storage_uri="memory://",
    headers_enabled=True,  # Add X-RateLimit-* headers to responses
)


def rate_limit_exceeded_handler(request: Request, exc: Exception) -> Response:
    """Custom handler for rate limit exceeded errors.

    Provides a consistent JSON error response when rate limits are exceeded.

    Args:
        request: FastAPI request object
        exc: Exception (should be RateLimitExceeded)

    Returns:
        JSON response with rate limit error details and Retry-After header
    """
    # Cast to RateLimitExceeded to access detail attribute
    if isinstance(exc, RateLimitExceeded):
        detail = exc.detail
    else:
        detail = str(exc)

    return Response(
        content=f'{{"error": "Rate limit exceeded", "detail": "{detail}"}}',
        status_code=HTTP_429_TOO_MANY_REQUESTS,
        media_type="application/json",
        headers={"Retry-After": "60"},
    )
