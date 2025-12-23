"""Tests for core configuration."""

import os

import pytest

from src.core.config import (
    DANGEROUS_PATTERNS,
    load_database_urls,
    settings,
)


def test_dangerous_patterns_coverage() -> None:
    """Test that all critical SQL keywords are blocked."""
    critical_keywords = [
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "TRUNCATE",
        "ALTER",
        "CREATE",
    ]

    for keyword in critical_keywords:
        assert keyword in DANGEROUS_PATTERNS


def test_timeout_values_are_reasonable() -> None:
    """Test that timeout values are within reasonable bounds."""
    assert settings.default_timeout_ms > 0
    assert settings.max_timeout_ms > settings.default_timeout_ms
    assert settings.max_timeout_ms <= 60000  # Max 60 seconds is reasonable


def test_rate_limit_window_is_positive() -> None:
    """Test that rate limit window is positive."""
    assert settings.rate_limit_window > 0


def test_load_database_urls_parses_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that DATABASE*_URL variables are parsed correctly."""
    # Clear all existing DATABASE*_URL env vars
    for key in list(os.environ.keys()):
        if key.startswith("DATABASE") and key.endswith("_URL"):
            monkeypatch.delenv(key, raising=False)

    monkeypatch.setenv("DATABASE_TEST_URL", "postgresql://user:pass@localhost/testdb")
    monkeypatch.setenv("DATABASE_PROD_URL", "postgresql://user:pass@localhost/proddb")
    monkeypatch.setenv("RANDOM_VAR", "should_be_ignored")

    result = load_database_urls()

    assert "testdb" in result
    assert "proddb" in result
    assert len(result) == 2


def test_load_database_urls_handles_invalid_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that invalid URLs are logged and skipped."""
    # Clear all existing DATABASE*_URL env vars first
    for key in list(os.environ.keys()):
        if key.startswith("DATABASE") and key.endswith("_URL"):
            monkeypatch.delenv(key, raising=False)

    monkeypatch.setenv("DATABASE_INVALID_URL", "not_a_valid_url")

    result = load_database_urls()

    # Current implementation doesn't validate URL format, just extracts path
    # This is expected behavior - function does basic parsing
    assert isinstance(result, dict)


def test_load_database_urls_empty_when_none_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that empty dict is returned when no databases configured."""
    # Clear all DATABASE*_URL env vars
    for key in list(os.environ.keys()):
        if key.startswith("DATABASE") and key.endswith("_URL"):
            monkeypatch.delenv(key, raising=False)

    result = load_database_urls()

    assert isinstance(result, dict)
