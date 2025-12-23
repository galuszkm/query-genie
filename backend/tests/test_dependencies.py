"""Unit tests for API dependencies."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from src.api.dependencies import get_redis_client, require_api_key, set_redis_client
from src.utils.redis_client import RedisClient


class TestGetRedisClient:
    """Test get_redis_client dependency."""

    @pytest.mark.asyncio
    async def test_returns_client_when_initialized(self) -> None:
        """Test that client is returned when properly initialized."""
        mock_request = MagicMock()
        mock_redis_client = MagicMock(spec=RedisClient)
        mock_redis_instance = AsyncMock()
        mock_redis_client.client = mock_redis_instance
        mock_request.app.state.redis_client = mock_redis_client

        result = await get_redis_client(mock_request)
        assert result == mock_redis_instance

    @pytest.mark.asyncio
    async def test_raises_503_when_no_state(self) -> None:
        """Test that 503 is raised when redis_client not in state."""
        mock_request = MagicMock()
        # Simulate missing attribute
        del mock_request.app.state.redis_client

        with pytest.raises(HTTPException) as exc_info:
            await get_redis_client(mock_request)
        assert exc_info.value.status_code == 503
        assert "not initialized" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_raises_503_when_none(self) -> None:
        """Test that 503 is raised when redis_client is None."""
        mock_request = MagicMock()
        mock_request.app.state.redis_client = None

        with pytest.raises(HTTPException) as exc_info:
            await get_redis_client(mock_request)
        assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_raises_503_when_wrong_type(self) -> None:
        """Test that 503 is raised when redis_client is wrong type."""
        mock_request = MagicMock()
        mock_request.app.state.redis_client = "not a redis client"

        with pytest.raises(HTTPException) as exc_info:
            await get_redis_client(mock_request)
        assert exc_info.value.status_code == 503
        assert "Invalid" in exc_info.value.detail


class TestSetRedisClient:
    """Test set_redis_client helper."""

    def test_sets_client_on_state(self) -> None:
        """Test that client is set on app state."""
        mock_state = MagicMock()
        mock_client = MagicMock(spec=RedisClient)

        set_redis_client(mock_state, mock_client)
        assert mock_state.redis_client == mock_client

    def test_sets_none_on_state(self) -> None:
        """Test that None can be set on app state."""
        mock_state = MagicMock()

        set_redis_client(mock_state, None)
        assert mock_state.redis_client is None


class TestRequireApiKey:
    """Test require_api_key dependency."""

    @pytest.mark.asyncio
    async def test_no_api_key_configured_allows_access(self) -> None:
        """Test that no API key configured allows all requests."""
        # When no key is configured, access should be allowed
        # even without a header
        await require_api_key(None)  # Should not raise

    @pytest.mark.asyncio
    async def test_valid_api_key_passes(self) -> None:
        """Test that valid API key passes authentication."""
        import os
        from unittest.mock import patch

        test_key = "test-secret-key-12345"
        with patch.dict(os.environ, {"API_KEY": test_key}, clear=False):
            from src import config

            # Need to reload the settings with new env var
            original_settings = config.settings
            try:
                config.settings = config.Settings()
                # This should not raise
                await require_api_key(test_key)
            finally:
                config.settings = original_settings

    @pytest.mark.asyncio
    async def test_invalid_api_key_raises_401(self) -> None:
        """Test that invalid API key raises 401."""
        from unittest.mock import MagicMock, patch

        # Create mock settings with API key set
        mock_settings = MagicMock()
        mock_settings.api_key = MagicMock()
        mock_settings.api_key.get_secret_value.return_value = "test-secret-key-12345"

        import src.api.dependencies as deps_module

        with patch.object(deps_module, "settings", mock_settings):
            with pytest.raises(HTTPException) as exc_info:
                await deps_module.require_api_key("wrong-key")
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_api_key_raises_401(self) -> None:
        """Test that missing API key raises 401 when required."""
        from unittest.mock import MagicMock, patch

        # Create mock settings with API key set
        mock_settings = MagicMock()
        mock_settings.api_key = MagicMock()
        mock_settings.api_key.get_secret_value.return_value = "test-secret-key-12345"

        import src.api.dependencies as deps_module

        with patch.object(deps_module, "settings", mock_settings):
            with pytest.raises(HTTPException) as exc_info:
                await deps_module.require_api_key(None)
            assert exc_info.value.status_code == 401
