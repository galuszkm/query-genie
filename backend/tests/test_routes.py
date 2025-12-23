"""Unit tests for API routes."""

import json
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from src.api.routes import router
from src.config import QUESTION_PROPOSALS, WELCOME_CONFIG


@pytest.fixture
def app() -> FastAPI:
    """Create test FastAPI app."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(app)


class TestWelcomeEndpoint:
    """Test /welcome endpoint."""

    def test_returns_welcome_config(self, client: TestClient) -> None:
        """Test that welcome endpoint returns config and suggestions."""
        response = client.get("/ai/api/welcome")

        assert response.status_code == 200
        data = response.json()

        assert "title" in data
        assert "subtitle" in data
        assert "suggestions" in data
        assert data["title"] == WELCOME_CONFIG["title"]
        assert data["subtitle"] == WELCOME_CONFIG["subtitle"]
        assert data["suggestions"] == QUESTION_PROPOSALS


class TestSuggestionsEndpoint:
    """Test /suggestions endpoint."""

    def test_returns_question_proposals(self, client: TestClient) -> None:
        """Test that suggestions endpoint returns question list."""
        response = client.get("/ai/api/suggestions")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert data == QUESTION_PROPOSALS


class TestHealthEndpoint:
    """Test /health endpoint."""

    def test_health_check_healthy_when_redis_ok(
        self, app: FastAPI, client: TestClient
    ) -> None:
        """Test health endpoint when Redis is healthy."""
        # Mock Redis client in app state
        mock_redis_client = MagicMock()
        mock_redis_instance = AsyncMock()
        mock_redis_instance.ping = AsyncMock(return_value=True)
        mock_redis_client.client = mock_redis_instance
        app.state.redis_client = mock_redis_client

        response = client.get("/ai/api/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert data["redis_status"] == "ok"

    def test_health_check_degraded_when_redis_fails(
        self, app: FastAPI, client: TestClient
    ) -> None:
        """Test health endpoint when Redis connection fails."""
        # Mock Redis client that raises error
        mock_redis_client = MagicMock()
        mock_redis_instance = AsyncMock()
        mock_redis_instance.ping = AsyncMock(
            side_effect=Exception("Connection refused")
        )
        mock_redis_client.client = mock_redis_instance
        app.state.redis_client = mock_redis_client

        response = client.get("/ai/api/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "degraded"
        assert "error" in data["redis_status"]

    def test_health_check_skips_when_no_redis_client(
        self, app: FastAPI, client: TestClient
    ) -> None:
        """Test health endpoint when Redis client not configured."""
        # Ensure no redis_client in app state
        if hasattr(app.state, "redis_client"):
            delattr(app.state, "redis_client")

        response = client.get("/ai/api/health")

        assert response.status_code == 200
        data = response.json()

        assert data["redis_status"] == "skipped"
        assert data["status"] == "degraded"


class TestChatStreamEndpoint:
    """Test /chat/stream endpoint."""

    @pytest.mark.asyncio
    async def test_chat_stream_requires_auth(self, app: FastAPI) -> None:
        """Test that chat stream requires API key when configured."""
        # Set up Redis client in app state
        mock_redis_client = MagicMock()
        app.state.redis_client = mock_redis_client

        # Set API key in settings to enable auth
        with patch("src.api.dependencies.settings") as mock_settings:
            mock_settings.api_key.get_secret_value.return_value = "test-key"

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.post(
                    "/ai/api/chat/stream",
                    json={"message": "Hello"},
                )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_chat_stream_with_valid_auth(self, app: FastAPI) -> None:
        """Test chat stream with valid API key."""
        # Mock Redis client
        mock_redis = AsyncMock()
        mock_redis.lpush = AsyncMock()

        # Mock pubsub
        mock_pubsub = AsyncMock()
        mock_pubsub.subscribe = AsyncMock()
        mock_pubsub.unsubscribe = AsyncMock()
        mock_pubsub.close = AsyncMock()

        # Mock listen to yield test events
        async def mock_listen() -> AsyncIterator[dict[str, Any]]:
            events = [
                {"data": json.dumps({"type": "session", "session_id": "test-123"})},
                {"data": json.dumps({"type": "token", "text": "Hello"})},
                {"data": json.dumps({"type": "complete", "message": "Done"})},
            ]
            for event in events:
                yield event

        mock_pubsub.listen = mock_listen
        mock_redis.pubsub = MagicMock(return_value=mock_pubsub)

        # Add mock redis to app dependencies
        app.dependency_overrides = {}

        async def override_redis() -> AsyncMock:
            return mock_redis

        async def override_auth() -> bool:
            return True

        from src.api.dependencies import get_redis_client, require_api_key

        app.dependency_overrides[get_redis_client] = override_redis
        app.dependency_overrides[require_api_key] = override_auth

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/ai/api/chat/stream",
                json={"message": "Test message"},
                headers={"Accept": "text/event-stream"},
            )

        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_chat_stream_handles_errors(self, app: FastAPI) -> None:
        """Test chat stream handles errors gracefully."""
        # Mock Redis client that raises error
        mock_redis = AsyncMock()
        mock_redis.lpush = AsyncMock(side_effect=Exception("Redis error"))

        async def override_redis() -> AsyncMock:
            return mock_redis

        async def override_auth() -> bool:
            return True

        from src.api.dependencies import get_redis_client, require_api_key

        app.dependency_overrides[get_redis_client] = override_redis
        app.dependency_overrides[require_api_key] = override_auth

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/ai/api/chat/stream",
                json={"message": "Test"},
                headers={"Accept": "text/event-stream"},
            )

        # Should still return 200 but with error event in stream
        assert response.status_code == 200


class TestSessionEndpoint:
    """Test /session/{session_id} endpoint."""

    def test_session_requires_auth(self, app: FastAPI, client: TestClient) -> None:
        """Test that session endpoint requires API key when configured."""
        # Set API key in settings to enable auth
        with patch("src.api.dependencies.settings") as mock_settings:
            mock_settings.api_key.get_secret_value.return_value = "test-key"

            response = client.get("/ai/api/session/test-session-123")

            assert response.status_code == 401

    @patch("src.api.routes.get_session_info")
    def test_session_returns_info_when_exists(
        self, mock_get_session_info: Any, app: FastAPI, client: TestClient
    ) -> None:
        """Test session endpoint returns session info."""
        # Mock session info
        mock_get_session_info.return_value = {
            "session_id": "test-123",
            "created_at": "2025-12-23T10:00:00",
            "metrics": {"total_tokens": 100},
        }

        # Override auth
        async def override_auth() -> bool:
            return True

        from src.api.dependencies import require_api_key

        app.dependency_overrides[require_api_key] = override_auth

        response = client.get("/ai/api/session/test-123")

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test-123"
        assert "metrics" in data

    @patch("src.api.routes.get_session_info")
    def test_session_returns_404_when_not_found(
        self, mock_get_session_info: Any, app: FastAPI, client: TestClient
    ) -> None:
        """Test session endpoint returns 404 for missing session."""
        # Mock session not found
        mock_get_session_info.return_value = None

        # Override auth
        async def override_auth() -> bool:
            return True

        from src.api.dependencies import require_api_key

        app.dependency_overrides[require_api_key] = override_auth

        response = client.get("/ai/api/session/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
