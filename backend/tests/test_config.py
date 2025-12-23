"""Unit tests for backend configuration."""

import os
from typing import Any
from unittest.mock import patch


class TestSettingsAllowedOrigins:
    """Test get_allowed_origins method behavior."""

    def test_production_returns_empty_list(self) -> None:
        """Test that production environment returns empty CORS list."""
        env_vars: dict[str, Any] = {
            "ENVIRONMENT": "production",
            "ALLOWED_ORIGINS": "http://example.com",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            # Force reload settings
            from src.config import Settings

            settings = Settings()
            result = settings.get_allowed_origins()
            assert result == []

    def test_prod_alias_returns_empty_list(self) -> None:
        """Test that 'prod' alias also returns empty CORS list."""
        env_vars: dict[str, Any] = {"ENVIRONMENT": "prod"}
        with patch.dict(os.environ, env_vars, clear=False):
            from src.config import Settings

            settings = Settings()
            result = settings.get_allowed_origins()
            assert result == []

    def test_staging_returns_empty_list(self) -> None:
        """Test that staging environment returns empty CORS list."""
        env_vars: dict[str, Any] = {"ENVIRONMENT": "staging"}
        with patch.dict(os.environ, env_vars, clear=False):
            from src.config import Settings

            settings = Settings()
            result = settings.get_allowed_origins()
            assert result == []

    def test_development_with_configured_origins(self) -> None:
        """Test that development mode respects configured origins."""
        env_vars: dict[str, Any] = {
            "ENVIRONMENT": "development",
            "ALLOWED_ORIGINS": "http://localhost:3000,http://myapp.local:8080",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            from src.config import Settings

            settings = Settings()
            result = settings.get_allowed_origins()
            assert "http://localhost:3000" in result
            assert "http://myapp.local:8080" in result
            assert len(result) == 2

    def test_development_default_origins(self) -> None:
        """Test that development mode returns default origins when none configured."""
        env_vars: dict[str, Any] = {"ENVIRONMENT": "development", "ALLOWED_ORIGINS": ""}
        with patch.dict(os.environ, env_vars, clear=False):
            from src.config import Settings

            settings = Settings()
            result = settings.get_allowed_origins()
            assert "http://localhost:5173" in result
            assert "http://localhost:3000" in result

    def test_origin_list_strips_whitespace(self) -> None:
        """Test that origin list items have whitespace stripped."""
        env_vars: dict[str, Any] = {
            "ENVIRONMENT": "development",
            "ALLOWED_ORIGINS": "  http://a.com  ,  http://b.com  ",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            from src.config import Settings

            settings = Settings()
            result = settings.get_allowed_origins()
            assert "http://a.com" in result
            assert "http://b.com" in result
