"""Unit tests for agent service Redis client operations."""

import json
from unittest.mock import AsyncMock

import pytest

from src.events.redis_client import (
    is_task_cancelled,
    mark_task_cancelled,
    pop_task,
    publish_event,
)


class TestPopTask:
    """Test pop_task function."""

    @pytest.mark.asyncio
    async def test_returns_task_when_available(self) -> None:
        """Test that task is returned when queue has item."""
        mock_redis = AsyncMock()
        task_data = {"task_id": "123", "message": "Hello"}
        mock_redis.brpop.return_value = ("agent:tasks", json.dumps(task_data))

        result = await pop_task(mock_redis, "agent:tasks", timeout=1)

        assert result == task_data
        mock_redis.brpop.assert_called_once_with("agent:tasks", timeout=1)

    @pytest.mark.asyncio
    async def test_returns_none_on_timeout(self) -> None:
        """Test that None is returned when timeout occurs."""
        mock_redis = AsyncMock()
        mock_redis.brpop.return_value = None

        result = await pop_task(mock_redis, "agent:tasks", timeout=1)

        assert result is None

    @pytest.mark.asyncio
    async def test_default_timeout_is_zero(self) -> None:
        """Test that default timeout is 0 (blocking)."""
        mock_redis = AsyncMock()
        mock_redis.brpop.return_value = None

        await pop_task(mock_redis, "agent:tasks")

        mock_redis.brpop.assert_called_once_with("agent:tasks", timeout=0)


class TestPublishEvent:
    """Test publish_event function."""

    @pytest.mark.asyncio
    async def test_publishes_to_correct_channel(self) -> None:
        """Test that event is published to task:{id} channel."""
        mock_redis = AsyncMock()
        event = {"type": "token", "content": "Hello"}

        await publish_event(mock_redis, "task-123", event)

        mock_redis.publish.assert_called_once()
        call_args = mock_redis.publish.call_args
        assert call_args[0][0] == "task:task-123"
        assert json.loads(call_args[0][1]) == event


class TestIsTaskCancelled:
    """Test is_task_cancelled function."""

    @pytest.mark.asyncio
    async def test_returns_true_when_cancelled(self) -> None:
        """Test that True is returned when cancel key exists."""
        mock_redis = AsyncMock()
        mock_redis.exists.return_value = 1

        is_cancelled, new_last_check = await is_task_cancelled(
            mock_redis, "task-123", current_time=10.0, last_check=0.0
        )

        assert is_cancelled is True
        assert new_last_check == 10.0
        mock_redis.exists.assert_called_once_with("task:task-123:cancelled")

    @pytest.mark.asyncio
    async def test_returns_false_when_not_cancelled(self) -> None:
        """Test that False is returned when cancel key doesn't exist."""
        mock_redis = AsyncMock()
        mock_redis.exists.return_value = 0

        is_cancelled, new_last_check = await is_task_cancelled(
            mock_redis, "task-123", current_time=10.0, last_check=0.0
        )

        assert is_cancelled is False
        assert new_last_check == 10.0

    @pytest.mark.asyncio
    async def test_skips_check_when_interval_not_elapsed(self) -> None:
        """Test that Redis check is skipped when not enough time has elapsed."""
        mock_redis = AsyncMock()
        mock_redis.exists.return_value = 1

        # Current time is only 2 seconds after last check (less than 5 second interval)
        is_cancelled, new_last_check = await is_task_cancelled(
            mock_redis, "task-123", current_time=7.0, last_check=5.0
        )

        # Should return False and not update last_check
        assert is_cancelled is False
        assert new_last_check == 5.0
        # Redis should not have been called
        mock_redis.exists.assert_not_called()

    @pytest.mark.asyncio
    async def test_checks_redis_when_interval_elapsed(self) -> None:
        """Test that Redis check occurs when enough time has elapsed."""
        mock_redis = AsyncMock()
        mock_redis.exists.return_value = 1

        # Current time is 6 seconds after last check (more than 5 second interval)
        is_cancelled, new_last_check = await is_task_cancelled(
            mock_redis, "task-123", current_time=11.0, last_check=5.0
        )

        # Should check Redis and update last_check
        assert is_cancelled is True
        assert new_last_check == 11.0
        mock_redis.exists.assert_called_once_with("task:task-123:cancelled")


class TestMarkTaskCancelled:
    """Test mark_task_cancelled function."""

    @pytest.mark.asyncio
    async def test_sets_cancel_key_with_ttl(self) -> None:
        """Test that cancel key is set with TTL."""
        mock_redis = AsyncMock()

        await mark_task_cancelled(mock_redis, "task-123", ttl_seconds=300)

        mock_redis.setex.assert_called_once_with("task:task-123:cancelled", 300, "1")

    @pytest.mark.asyncio
    async def test_default_ttl_is_300(self) -> None:
        """Test that default TTL is 300 seconds."""
        mock_redis = AsyncMock()

        await mark_task_cancelled(mock_redis, "task-123")

        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == 300  # TTL
