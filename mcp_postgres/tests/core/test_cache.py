"""Tests for core cache functionality."""

import time

from pytest_mock import MockerFixture

from src.core.cache import (
    SCHEMA_CACHE_TTL,
    get_cached_schema,
    set_cached_schema,
)


def test_cache_miss_returns_none() -> None:
    """Test that missing cache entry returns None."""
    result = get_cached_schema("nonexistent_db", "nonexistent_table")
    assert result is None


def test_cache_hit_returns_data() -> None:
    """Test that valid cache entry is returned."""
    set_cached_schema("test_db", "test_table", "cached_data")
    result = get_cached_schema("test_db", "test_table")
    assert result == "cached_data"


def test_cache_expiration(mocker: MockerFixture) -> None:
    """Test that expired cache entries return None."""
    set_cached_schema("test_db", "test_table", "old_data")

    # Mock time to simulate expiration
    future_time = time.time() + SCHEMA_CACHE_TTL + 1
    mocker.patch("src.core.cache.time.time", return_value=future_time)

    result = get_cached_schema("test_db", "test_table")
    assert result is None


def test_cache_key_uniqueness() -> None:
    """Test that different db/table combinations have separate cache entries."""
    set_cached_schema("db1", "table1", "data1")
    set_cached_schema("db2", "table1", "data2")
    set_cached_schema("db1", "table2", "data3")

    assert get_cached_schema("db1", "table1") == "data1"
    assert get_cached_schema("db2", "table1") == "data2"
    assert get_cached_schema("db1", "table2") == "data3"


def test_cache_overwrite() -> None:
    """Test that setting cache twice overwrites previous value."""
    set_cached_schema("test_db", "test_table", "old_data")
    set_cached_schema("test_db", "test_table", "new_data")

    result = get_cached_schema("test_db", "test_table")
    assert result == "new_data"
