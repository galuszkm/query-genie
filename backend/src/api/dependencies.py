"""API dependencies for dependency injection.

Provides Redis client injection for worker communication.
"""

from typing import Annotated

import redis.asyncio as redis
from fastapi import Depends, Header, HTTPException, Request

from ..config import settings
from ..utils.redis_client import RedisClient


async def get_redis_client(request: Request) -> redis.Redis:
    """Get the Redis client instance from app state.

    Args:
        request: FastAPI request object

    Raises:
        HTTPException: If Redis client is not initialized

    Returns:
        Redis client instance
    """
    if not hasattr(request.app.state, "redis_client"):
        raise HTTPException(status_code=503, detail="Redis client not initialized")

    client = request.app.state.redis_client
    if client is None:
        raise HTTPException(status_code=503, detail="Redis client not initialized")

    if not isinstance(client, RedisClient):
        raise HTTPException(status_code=503, detail="Invalid Redis client type")

    return client.client


def set_redis_client(app_state: object, client: RedisClient | None) -> None:
    """Set the Redis client instance in app state.

    Args:
        app_state: FastAPI app state object
        client: RedisClient instance or None
    """
    app_state.redis_client = client  # type: ignore[attr-defined]


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Optional API key authentication guard.

    Args:
        x_api_key: API key from X-API-Key header

    Raises:
        HTTPException: If API key is required but invalid/missing
    """
    api_key = settings.api_key.get_secret_value() if settings.api_key else None
    if api_key and x_api_key != api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


# Type aliases for dependency injection
RedisDep = Annotated[redis.Redis, Depends(get_redis_client)]
