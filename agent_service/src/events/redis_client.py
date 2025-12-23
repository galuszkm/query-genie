"""Redis client operations for agent service.

Handles:
- Task consumption from queue (BRPOP)
- Event publishing to Pub/Sub
- Cancellation tracking
"""

import asyncio
import json
from typing import Any

import redis.asyncio as redis

from ..core import settings
from ..utils import get_logger

logger = get_logger(__name__)


async def create_redis_client(
    max_retries: int = 5, initial_delay: float = 1.0
) -> redis.Redis:
    """Create and connect Redis client with exponential backoff retry.

    Args:
        max_retries: Maximum number of connection attempts
        initial_delay: Initial delay between retries in seconds (doubles each retry)

    Returns:
        Connected Redis client

    Raises:
        ConnectionError: If unable to connect to Redis after all retries
    """
    delay = initial_delay
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            client: redis.Redis = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            await client.ping()
            logger.info(f"Connected to Redis: {settings.redis_url}")
            return client
        except (redis.ConnectionError, redis.TimeoutError, OSError) as e:
            last_error = e
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

    # Should never reach here, but for type safety
    raise ConnectionError(f"Unable to connect to Redis: {last_error}")


async def pop_task(
    redis_client: redis.Redis,
    queue: str,
    timeout: int = 0,
) -> dict[str, Any] | None:
    """Pop a task from the queue using BRPOP.

    BRPOP (Blocking Right Pop) blocks until an item is available or timeout.
    - timeout=0 means block indefinitely until an item arrives
    - Returns the oldest item in the queue (FIFO order)
    - Atomic operation - no race conditions with multiple workers

    Advantages over polling:
    - No CPU waste on empty queue
    - Immediate response when task arrives
    - Built-in blocking - no need for sleep loops

    Limitations:
    - Connection stays open during block
    - Timeout affects how quickly worker can shutdown
    - One connection per blocking call

    Args:
        redis_client: Connected Redis client
        queue: Queue name to pop from
        timeout: Seconds to wait (0 = forever)

    Returns:
        Task dictionary or None if timeout
    """
    result = await redis_client.brpop(queue, timeout=timeout)
    if result:
        _, task_json = result
        task: dict[str, Any] = json.loads(task_json)
        return task
    return None


async def publish_event(
    redis_client: redis.Redis,
    task_id: str,
    event: dict[str, Any],
) -> None:
    """Publish event to Redis Pub/Sub channel.

    Events are published to task:{task_id} channel for SSE forwarding.

    Args:
        redis_client: Connected Redis client
        task_id: Task identifier for the pub/sub channel
        event: Event data to publish
    """
    channel = f"task:{task_id}"
    event_json = json.dumps(event)
    await redis_client.publish(channel, event_json)
    logger.debug(f"Published event to {channel}: {event.get('type')}")


async def is_task_cancelled(redis_client: redis.Redis, task_id: str) -> bool:
    """Check if a task has been cancelled.

    Args:
        redis_client: Connected Redis client
        task_id: Task identifier to check

    Returns:
        True if task is cancelled
    """
    cancelled_key = f"task:{task_id}:cancelled"
    exists: int = await redis_client.exists(cancelled_key)
    return exists > 0


async def mark_task_cancelled(
    redis_client: redis.Redis,
    task_id: str,
    ttl_seconds: int = 300,
) -> None:
    """Mark a task as cancelled.

    Args:
        redis_client: Connected Redis client
        task_id: Task identifier to cancel
        ttl_seconds: How long to keep the cancellation marker
    """
    cancelled_key = f"task:{task_id}:cancelled"
    await redis_client.setex(cancelled_key, ttl_seconds, "1")
    logger.info(f"Task {task_id[:8]} marked as cancelled")
