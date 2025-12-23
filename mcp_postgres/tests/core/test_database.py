"""Tests for core database functionality."""

from typing import Any

import pytest
from pytest_mock import MockerFixture

from src.core.database import async_connection, close_pools, get_async_pool


@pytest.mark.asyncio
async def test_get_async_pool_creates_pool(mocker: MockerFixture) -> None:
    """Test that pool is created on first access."""
    mocker.patch(
        "src.core.database.DATABASE_URLS", {"test_db": "postgresql://localhost/test"}
    )

    mock_pool = mocker.AsyncMock()

    async def mock_create_pool(*args: Any, **kwargs: Any) -> Any:
        return mock_pool

    mocker.patch("src.core.database.asyncpg.create_pool", side_effect=mock_create_pool)

    await close_pools()  # Clear any existing pools

    pool = await get_async_pool("test_db")

    assert pool is not None


@pytest.mark.asyncio
async def test_get_async_pool_reuses_existing(mocker: MockerFixture) -> None:
    """Test that existing pool is reused."""
    mocker.patch(
        "src.core.database.DATABASE_URLS", {"test_db": "postgresql://localhost/test"}
    )

    mock_pool = mocker.AsyncMock()
    call_count = [0]

    async def mock_create_pool(*args: Any, **kwargs: Any) -> Any:
        call_count[0] += 1
        return mock_pool

    mocker.patch("src.core.database.asyncpg.create_pool", side_effect=mock_create_pool)

    await close_pools()

    pool1 = await get_async_pool("test_db")
    pool2 = await get_async_pool("test_db")

    assert pool1 is pool2
    assert call_count[0] == 1


@pytest.mark.asyncio
async def test_get_async_pool_invalid_database(mocker: MockerFixture) -> None:
    """Test error when database not configured."""
    mocker.patch(
        "src.core.database.DATABASE_URLS", {"valid_db": "postgresql://localhost/valid"}
    )

    with pytest.raises(ValueError, match="not configured"):
        await get_async_pool("invalid_db")


@pytest.mark.asyncio
async def test_async_connection_sets_timeout(mocker: MockerFixture) -> None:
    """Test that connection sets statement timeout."""
    mocker.patch(
        "src.core.database.DATABASE_URLS", {"test_db": "postgresql://localhost/test"}
    )

    mock_conn = mocker.AsyncMock()
    mock_pool = mocker.MagicMock()

    # Create proper async context manager
    class MockAcquire:
        async def __aenter__(self) -> Any:
            return mock_conn

        async def __aexit__(self, *args: Any) -> None:
            pass

    mock_pool.acquire.return_value = MockAcquire()

    async def mock_get_pool(db: str) -> Any:
        return mock_pool

    mocker.patch("src.core.database.get_async_pool", side_effect=mock_get_pool)

    async with async_connection("test_db", timeout_ms=10000):
        pass

    mock_conn.execute.assert_called_once()
    call_args = mock_conn.execute.call_args[0][0]
    assert "SET statement_timeout" in call_args


@pytest.mark.asyncio
async def test_async_connection_clamps_timeout(mocker: MockerFixture) -> None:
    """Test that timeout is clamped to valid range."""
    mocker.patch(
        "src.core.database.DATABASE_URLS", {"test_db": "postgresql://localhost/test"}
    )
    mocker.patch("src.core.config.settings.max_timeout_ms", 30000)

    mock_conn = mocker.AsyncMock()
    mock_pool = mocker.MagicMock()

    # Create proper async context manager
    class MockAcquire:
        async def __aenter__(self) -> Any:
            return mock_conn

        async def __aexit__(self, *args: Any) -> None:
            pass

    mock_pool.acquire.return_value = MockAcquire()

    async def mock_get_pool(db: str) -> Any:
        return mock_pool

    mocker.patch("src.core.database.get_async_pool", side_effect=mock_get_pool)

    # Test too high timeout gets clamped
    async with async_connection("test_db", timeout_ms=99999):
        pass

    call_args = mock_conn.execute.call_args[0][0]
    assert "30000" in call_args


@pytest.mark.asyncio
async def test_close_pools_clears_cache(mocker: MockerFixture) -> None:
    """Test that close_pools clears the pool cache and closes pools gracefully."""
    from src.core.database import _ASYNC_POOLS

    # Create a mock pool with close method
    mock_pool = mocker.AsyncMock()
    _ASYNC_POOLS["test"] = mock_pool

    await close_pools()

    # Verify pool.close() was called
    mock_pool.close.assert_awaited_once()
    # Verify cache was cleared
    assert len(_ASYNC_POOLS) == 0
