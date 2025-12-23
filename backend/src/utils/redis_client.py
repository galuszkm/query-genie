"""Redis client utilities for task queue and event streaming.

Provides functions for:
- Enqueuing tasks to the agent service queue
- Subscribing to task events for SSE streaming
- Managing Redis connections in FastAPI context
"""

import asyncio
import json
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

import redis.asyncio as redis

from ..config import settings
from ..logging_config import get_logger

logger = get_logger(__name__)


class RedisClient:
    """Redis client wrapper for task queue and pub/sub operations.

    Handles:
    - Task enqueuing to worker queue
    - Event subscription for SSE streaming
    - Connection lifecycle management

    Architecture:
    - Single Redis client instance manages an internal connection pool
    - Each pubsub() call reuses connections from this shared pool
    - This is optimal for many concurrent SSE streams with task-based channels
    """

    def __init__(self) -> None:
        """Initialize Redis client (not connected yet)."""
        self._redis: redis.Redis | None = None

    async def connect(self, max_retries: int = 5, initial_delay: float = 1.0) -> None:
        """Establish connection to Redis server with exponential backoff retry.

        Args:
            max_retries: Maximum number of connection attempts
            initial_delay: Initial delay between retries in seconds (doubles each retry)

        Raises:
            ConnectionError: If unable to connect after all retries
        """
        delay = initial_delay

        for attempt in range(1, max_retries + 1):
            try:
                self._redis = redis.from_url(
                    settings.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
                await self._redis.ping()
                logger.info(f"Redis client connected: {settings.redis_url}")
                return
            except (redis.ConnectionError, redis.TimeoutError, OSError) as e:
                if attempt == max_retries:
                    logger.error(
                        f"Failed to connect to Redis after {max_retries} attempts: {e}"
                    )
                    raise ConnectionError(
                        f"Unable to connect to Redis at {settings.redis_url} after {max_retries} attempts"
                    ) from e

                logger.warning(
                    f"Redis connection attempt {attempt}/{max_retries} failed: {e}. "
                    f"Retrying in {delay:.1f}s..."
                )
                await asyncio.sleep(delay)
                delay *= 2  # Exponential backoff

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            logger.info("Redis client disconnected")

    @property
    def client(self) -> redis.Redis:
        """Get the Redis client instance.

        Raises:
            RuntimeError: If not connected
        """
        if not self._redis:
            raise RuntimeError("Redis client not connected")
        return self._redis


async def enqueue_task(
    redis_client: redis.Redis,
    message: str,
    session_id: str | None = None,
) -> dict[str, str]:
    """Enqueue a chat task to the worker queue.

    Args:
        redis_client: Connected Redis client
        message: User message to process
        session_id: Optional session ID (generates new if None)

    Returns:
        Dictionary with task_id and session_id
    """
    task_id = str(uuid.uuid4())
    if not session_id:
        session_id = str(uuid.uuid4())

    task = {
        "task_id": task_id,
        "session_id": session_id,
        "message": message,
        "created_at": datetime.now(UTC).isoformat(),
    }

    await redis_client.lpush(settings.redis_task_queue, json.dumps(task))
    logger.info(f"Enqueued task {task_id[:8]} for session {session_id[:8]}")

    return {"task_id": task_id, "session_id": session_id}


async def subscribe_task_events(
    redis_client: redis.Redis,
    task_id: str,
) -> AsyncGenerator[dict[str, Any]]:
    """Subscribe to events for a specific task.

    Yields events from Redis Pub/Sub channel until complete or error.

    Architecture Note:
    - Creates a new pubsub instance per task stream
    - This is optimal for task-based pub/sub with short-lived subscriptions
    - The underlying Redis client connection pool is shared across all pubsub instances
    - Each task has a unique channel (task:{task_id}) with a single consumer
    - Alternative global pubsub would require complex message routing and has no benefit here

    Args:
        redis_client: Connected Redis client (shared pool)
        task_id: Task ID to subscribe to

    Yields:
        Event dictionaries from the worker
    """
    # Create pubsub with ignore_subscribe_messages=True to skip control messages
    pubsub = redis_client.pubsub(ignore_subscribe_messages=True)
    channel = f"task:{task_id}"

    try:
        await pubsub.subscribe(channel)
        logger.debug(f"Subscribed to channel: {channel}")

        # With ignore_subscribe_messages=True, we only get actual messages
        async for message in pubsub.listen():
            event = json.loads(message["data"])
            yield event

            # Stop on terminal events
            if event.get("type") in ("complete", "error"):
                break

    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()
        logger.debug(f"Unsubscribed from channel: {channel}")


def create_session_event(session_id: str) -> dict[str, str]:
    """Create a session acknowledgment event.

    Args:
        session_id: Session identifier

    Returns:
        Session event dictionary
    """
    return {"type": "session", "session_id": session_id}


def create_error_event(message: str, session_id: str | None = None) -> dict[str, Any]:
    """Create an error event.

    Args:
        message: Error message
        session_id: Optional session ID

    Returns:
        Error event dictionary
    """
    event: dict[str, Any] = {"type": "error", "message": message}
    if session_id:
        event["session_id"] = session_id
    return event
