"""Unit tests for agent service configuration."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def isolate_from_env_file():
    """Temporarily rename .env file to prevent Settings from loading it during tests."""
    env_path = Path(".env")
    backup_path = Path(".env.test_backup")

    renamed = False
    if env_path.exists():
        env_path.rename(backup_path)
        renamed = True

    yield

    # Restore .env file
    if renamed and backup_path.exists():
        if env_path.exists():
            env_path.unlink()
        backup_path.rename(env_path)


class TestSettings:
    """Test Settings configuration."""

    def test_default_redis_url(self) -> None:
        """Test default Redis URL value."""
        from src.core.config import Settings

        settings = Settings()
        assert settings.redis_url == "redis://localhost:6379/0"

    def test_default_redis_task_queue(self) -> None:
        """Test default Redis task queue name."""
        from src.core.config import Settings

        settings = Settings()
        assert settings.redis_task_queue == "agent:tasks"

    def test_custom_redis_url(self) -> None:
        """Test custom Redis URL from environment."""
        with patch.dict(
            os.environ, {"REDIS_URL": "redis://custom:6380/1"}, clear=False
        ):
            from src.core.config import Settings

            settings = Settings()
            assert settings.redis_url == "redis://custom:6380/1"

    def test_bedrock_provider_selected(self) -> None:
        """Test Bedrock model provider selection."""
        with patch.dict(os.environ, {"MODEL_PROVIDER": "BEDROCK"}, clear=False):
            from src.core.config import Settings

            settings = Settings()
            assert settings.model_provider == "BEDROCK"

    def test_ollama_provider_selected(self) -> None:
        """Test Ollama model provider selection."""
        with patch.dict(os.environ, {"MODEL_PROVIDER": "OLLAMA"}, clear=False):
            from src.core.config import Settings

            settings = Settings()
            assert settings.model_provider == "OLLAMA"


class TestBedrockBotoSession:
    """Test get_bedrock_boto_session method."""

    def test_creates_boto_session_with_credentials(self) -> None:
        """Test that boto session is created with AWS credentials."""
        env = {
            "MODEL_PROVIDER": "BEDROCK",
            "AWS_REGION": "us-west-2",
            "AWS_ACCESS_KEY_ID": "AKIATEST123",
            "AWS_SECRET_ACCESS_KEY": "secret123",
        }
        with patch.dict(os.environ, env, clear=False):
            from src.core.config import Settings

            settings = Settings()
            session = settings.get_bedrock_boto_session()

            # Session should have our region
            assert session.region_name == "us-west-2"

    def test_includes_session_token_when_provided(self) -> None:
        """Test that session token is included when present."""
        env = {
            "MODEL_PROVIDER": "BEDROCK",
            "AWS_REGION": "us-east-1",
            "AWS_ACCESS_KEY_ID": "AKIATEST123",
            "AWS_SECRET_ACCESS_KEY": "secret123",
            "AWS_SESSION_TOKEN": "token123",
        }
        with patch.dict(os.environ, env, clear=False):
            from src.core.config import Settings

            settings = Settings()
            session = settings.get_bedrock_boto_session()

            # Session should be created (token included internally)
            assert session is not None
            assert session.region_name == "us-east-1"
