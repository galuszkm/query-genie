"""Unit tests for Redis client utilities."""

import json
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
import redis.asyncio as redis

from src.utils.redis_client import (
    RedisClient,
    create_error_event,
    create_session_event,
    enqueue_task,
    subscribe_task_events,
)


class TestRedisClient:
    """Test RedisClient class."""

    @pytest.mark.asyncio
    async def test_client_property_raises_when_not_connected(self) -> None:
        """Test that client property raises error when not connected."""
        client = RedisClient()
        with pytest.raises(RuntimeError, match="not connected"):
            _ = client.client

    @pytest.mark.asyncio
    async def test_connect_succeeds(self) -> None:
        """Test successful connection to Redis."""
        client = RedisClient()

        with patch("src.utils.redis_client.redis.from_url") as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock(return_value=True)
            mock_from_url.return_value = mock_redis

            await client.connect(max_retries=3, initial_delay=0.1)

            assert client._redis is not None
            mock_redis.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_retries_on_failure(self) -> None:
        """Test connection retry with exponential backoff."""
        client = RedisClient()

        call_count = 0

        def side_effect(*args: Any, **kwargs: Any) -> AsyncMock:
            nonlocal call_count
            call_count += 1
            mock_redis = AsyncMock()
            if call_count < 3:
                mock_redis.ping = AsyncMock(side_effect=redis.ConnectionError("Failed"))
            else:
                mock_redis.ping = AsyncMock(return_value=True)
            return mock_redis

        with (
            patch("src.utils.redis_client.redis.from_url") as mock_from_url,
            patch("src.utils.redis_client.asyncio.sleep") as mock_sleep,
        ):
            mock_from_url.side_effect = side_effect

            await client.connect(max_retries=5, initial_delay=0.1)

            assert call_count == 3
            assert mock_sleep.call_count == 2

    @pytest.mark.asyncio
    async def test_connect_fails_after_max_retries(self) -> None:
        """Test connection failure after exhausting retries."""
        client = RedisClient()

        with (
            patch("src.utils.redis_client.redis.from_url") as mock_from_url,
            patch("src.utils.redis_client.asyncio.sleep"),
        ):
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock(side_effect=redis.ConnectionError("Failed"))
            mock_from_url.return_value = mock_redis

            with pytest.raises(ConnectionError) as exc_info:
                await client.connect(max_retries=3, initial_delay=0.1)

            assert "after 3 attempts" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_disconnect_closes_connection(self) -> None:
        """Test disconnecting from Redis."""
        client = RedisClient()
        mock_redis = AsyncMock()
        client._redis = mock_redis

        await client.disconnect()

        mock_redis.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_when_not_connected(self) -> None:
        """Test disconnect does nothing when not connected."""
        client = RedisClient()

        # Should not raise error
        await client.disconnect()


class TestEnqueueTask:
    """Test enqueue_task function."""

    @pytest.mark.asyncio
    async def test_enqueue_with_session_id(self) -> None:
        """Test enqueueing task with provided session ID."""
        mock_redis = AsyncMock()
        mock_redis.lpush = AsyncMock()

        result = await enqueue_task(
            mock_redis,
            message="Hello",
            session_id="abc-123",
        )

        assert result["session_id"] == "abc-123"
        assert "task_id" in result
        mock_redis.lpush.assert_called_once()

        # Verify task structure
        call_args = mock_redis.lpush.call_args
        queue_name = call_args[0][0]
        task_json = call_args[0][1]
        task = json.loads(task_json)

        assert queue_name == "agent:tasks"
        assert task["message"] == "Hello"
        assert task["session_id"] == "abc-123"
        assert "created_at" in task

    @pytest.mark.asyncio
    async def test_enqueue_generates_session_id(self) -> None:
        """Test that session ID is generated when not provided."""
        mock_redis = AsyncMock()
        mock_redis.lpush = AsyncMock()

        result = await enqueue_task(
            mock_redis,
            message="Hello",
            session_id=None,
        )

        assert result["session_id"] is not None
        assert len(result["session_id"]) == 36  # UUID format


class TestSubscribeTaskEvents:
    """Test subscribe_task_events function."""

    @pytest.mark.asyncio
    async def test_subscribes_and_yields_events(self) -> None:
        """Test subscribing to task events and yielding them."""
        mock_redis = AsyncMock()
        mock_pubsub = AsyncMock()

        # Mock events from pubsub
        async def mock_listen() -> AsyncIterator[dict[str, Any]]:
            events = [
                {"data": json.dumps({"type": "token", "text": "Hello"})},
                {"data": json.dumps({"type": "complete", "message": "Done"})},
            ]
            for event in events:
                yield event

        mock_pubsub.listen = mock_listen
        mock_pubsub.subscribe = AsyncMock()
        mock_pubsub.unsubscribe = AsyncMock()
        mock_pubsub.close = AsyncMock()
        mock_redis.pubsub = lambda **kwargs: mock_pubsub

        events = []
        async for event in subscribe_task_events(mock_redis, "task-123"):
            events.append(event)

        assert len(events) == 2
        assert events[0]["type"] == "token"
        assert events[1]["type"] == "complete"
        mock_pubsub.subscribe.assert_called_once_with("task:task-123")
        mock_pubsub.unsubscribe.assert_called_once()
        mock_pubsub.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_stops_on_error_event(self) -> None:
        """Test that subscription stops on error event."""
        mock_redis = AsyncMock()
        mock_pubsub = AsyncMock()

        async def mock_listen() -> AsyncIterator[dict[str, Any]]:
            events = [
                {"data": json.dumps({"type": "token", "text": "Hi"})},
                {"data": json.dumps({"type": "error", "message": "Failed"})},
                {"data": json.dumps({"type": "token", "text": "Should not reach"})},
            ]
            for event in events:
                yield event

        mock_pubsub.listen = mock_listen
        mock_pubsub.subscribe = AsyncMock()
        mock_pubsub.unsubscribe = AsyncMock()
        mock_pubsub.close = AsyncMock()
        mock_redis.pubsub = lambda **kwargs: mock_pubsub

        events = []
        async for event in subscribe_task_events(mock_redis, "task-456"):
            events.append(event)

        assert len(events) == 2  # Should stop after error
        assert events[1]["type"] == "error"


class TestCreateSessionEvent:
    """Test create_session_event function."""

    def test_creates_session_event(self) -> None:
        """Test creating a session event."""
        event = create_session_event("session-123")

        assert event["type"] == "session"
        assert event["session_id"] == "session-123"


class TestCreateErrorEvent:
    """Test create_error_event function."""

    def test_creates_error_event(self) -> None:
        """Test creating an error event."""
        event = create_error_event("Something went wrong")

        assert event["type"] == "error"
        assert event["message"] == "Something went wrong"

    def test_includes_session_id(self) -> None:
        """Test that session ID is included when provided."""
        event = create_error_event("Error", session_id="sess-123")

        assert event["session_id"] == "sess-123"

    def test_excludes_session_id_when_none(self) -> None:
        """Test that session ID is not included when None."""
        event = create_error_event("Error", session_id=None)

        assert "session_id" not in event
