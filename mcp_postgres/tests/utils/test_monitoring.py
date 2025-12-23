"""Tests for monitoring utilities."""

import pytest
from pytest_mock import MockerFixture

from src.utils.monitoring import database_health


@pytest.mark.asyncio
async def test_database_health(mocker: MockerFixture) -> None:
    """Test database health check."""
    mock_conn = mocker.AsyncMock()
    # Mock sequence: fetchval(size), fetchval(cache_ratio)
    mock_conn.fetchval.side_effect = ["100 MB", 99.5]

    mock_ac = mocker.patch("src.utils.monitoring.async_connection")
    mock_ac.return_value.__aenter__.return_value = mock_conn
    mock_ac.return_value.__aexit__.return_value = None

    result = await database_health("test_db")

    assert "Database size: 100 MB" in result
    assert "Cache hit ratio: 99.5%" in result
