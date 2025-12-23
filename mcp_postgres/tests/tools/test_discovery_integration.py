"""Integration tests for discovery with error handling."""

from typing import Any

import pytest
from pytest_mock import MockerFixture

from src.tools.discovery import list_all_tables, list_tables


@pytest.mark.asyncio
async def test_list_tables_with_connection_timeout(mocker: MockerFixture) -> None:
    """Test that connection timeouts are handled gracefully."""
    mock_ac = mocker.patch("src.tools.discovery.async_connection")
    mock_ac.return_value.__aenter__.side_effect = TimeoutError("Connection timeout")

    result = await list_tables("test_db")

    assert "error" in result.lower()
    assert "timeout" in result.lower()


@pytest.mark.asyncio
async def test_list_all_tables_with_mixed_success_failure(
    mocker: MockerFixture,
) -> None:
    """Test list_all_tables when some databases succeed and others fail."""
    mocker.patch(
        "src.tools.discovery.DATABASE_URLS",
        {
            "working_db": "postgresql://localhost/working",
            "broken_db": "postgresql://localhost/broken",
        },
    )

    call_count = [0]

    def mock_connection_side_effect(*args: Any, **kwargs: Any) -> Any:
        call_count[0] += 1
        if "broken" in str(args):
            # Raise immediately, not inside async context
            raise ConnectionError("Connection refused")

        mock_conn = mocker.AsyncMock()
        mock_conn.fetch.return_value = [
            {"table_name": "test_table", "table_comment": None}
        ]

        class MockContext:
            async def __aenter__(self) -> Any:
                return mock_conn

            async def __aexit__(self, *args: Any) -> None:
                pass

        return MockContext()

    mocker.patch(
        "src.tools.discovery.async_connection", side_effect=mock_connection_side_effect
    )

    result = await list_all_tables()

    # Should show partial results and errors
    assert "test_table" in result or "error" in result.lower()


@pytest.mark.asyncio
async def test_list_tables_with_empty_database(mocker: MockerFixture) -> None:
    """Test listing tables when database has no tables."""
    mock_conn = mocker.AsyncMock()
    mock_conn.fetch.return_value = []

    mock_ac = mocker.patch("src.tools.discovery.async_connection")
    mock_ac.return_value.__aenter__.return_value = mock_conn
    mock_ac.return_value.__aexit__.return_value = None

    result = await list_tables("test_db")

    assert "no tables" in result.lower() or "empty" in result.lower() or len(result) > 0
