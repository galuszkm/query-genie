"""Tests for Redis reconnection logic."""

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
import redis.asyncio as redis


class TestRedisReconnection:
    """Test Redis connection retry logic."""

    @pytest.mark.asyncio
    async def test_retries_on_connection_failure(self) -> None:
        """Test that connection is retried with exponential backoff."""
        from src.events.redis_client import create_redis_client

        # Mock redis.from_url to fail twice, then succeed
        call_count = 0

        def side_effect_from_url(*args: Any, **kwargs: Any) -> AsyncMock:
            nonlocal call_count
            call_count += 1
            mock_client = AsyncMock()
            if call_count < 3:
                # First two attempts fail
                mock_client.ping = AsyncMock(
                    side_effect=redis.ConnectionError("Connection refused")
                )
            else:
                # Third attempt succeeds
                mock_client.ping = AsyncMock(return_value=True)
            return mock_client

        with (
            patch("src.events.redis_client.redis.from_url") as mock_from_url,
            patch("src.events.redis_client.asyncio.sleep") as mock_sleep,
        ):
            mock_from_url.side_effect = side_effect_from_url

            # Should succeed after 3 attempts
            await create_redis_client(max_retries=5, initial_delay=0.1)

            # Verify retries occurred
            assert mock_from_url.call_count == 3
            assert (
                mock_sleep.call_count == 2
            )  # Slept twice (after 1st and 2nd failures)

            # Verify exponential backoff
            sleep_calls = [call.args[0] for call in mock_sleep.call_args_list]
            assert sleep_calls[0] == 0.1  # First retry delay
            assert sleep_calls[1] == 0.2  # Second retry delay (doubled)

    @pytest.mark.asyncio
    async def test_fails_after_max_retries(self) -> None:
        """Test that connection fails after exhausting retries."""
        from src.events.redis_client import create_redis_client

        with (
            patch("src.events.redis_client.redis.from_url") as mock_from_url,
            patch("src.events.redis_client.asyncio.sleep") as mock_sleep,
        ):
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(
                side_effect=redis.ConnectionError("Connection refused")
            )
            mock_from_url.return_value = mock_client

            # Should fail after max_retries attempts
            with pytest.raises(ConnectionError) as exc_info:
                await create_redis_client(max_retries=3, initial_delay=0.1)

            assert "after 3 attempts" in str(exc_info.value)
            assert mock_from_url.call_count == 3
            assert (
                mock_sleep.call_count == 2
            )  # Slept after 1st and 2nd failures, not after 3rd

    @pytest.mark.asyncio
    async def test_succeeds_on_first_attempt(self) -> None:
        """Test that no retries occur when connection succeeds immediately."""
        from src.events.redis_client import create_redis_client

        with (
            patch("src.events.redis_client.redis.from_url") as mock_from_url,
            patch("src.events.redis_client.asyncio.sleep") as mock_sleep,
        ):
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(return_value=True)
            mock_from_url.return_value = mock_client

            # Should succeed immediately
            await create_redis_client(max_retries=5, initial_delay=0.1)

            # No retries needed
            assert mock_from_url.call_count == 1
            assert mock_sleep.call_count == 0
