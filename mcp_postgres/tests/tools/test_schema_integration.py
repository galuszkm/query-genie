"""Integration tests for schema tools with edge cases."""

import pytest
from pytest_mock import MockerFixture

from src.tools.schema import describe_table, describe_table_with_comments


@pytest.mark.asyncio
async def test_describe_table_not_found(mocker: MockerFixture) -> None:
    """Test describe_table when table doesn't exist."""
    mock_conn = mocker.AsyncMock()
    mock_conn.fetch.return_value = []  # No columns found

    mock_ac = mocker.patch("src.tools.schema.async_connection")
    mock_ac.return_value.__aenter__.return_value = mock_conn
    mock_ac.return_value.__aexit__.return_value = None

    result = await describe_table("test_db", "nonexistent_table")

    assert "not found" in result.lower()


@pytest.mark.asyncio
async def test_describe_table_with_schema_qualified_name(mocker: MockerFixture) -> None:
    """Test describe_table with schema-qualified table name."""
    mock_conn = mocker.AsyncMock()
    mock_conn.fetch.return_value = [
        {
            "column_name": "id",
            "data_type": "integer",
            "is_nullable": "NO",
            "column_default": None,
        }
    ]

    mock_ac = mocker.patch("src.tools.schema.async_connection")
    mock_ac.return_value.__aenter__.return_value = mock_conn
    mock_ac.return_value.__aexit__.return_value = None

    await describe_table("test_db", "public.users")

    # Should query the public schema
    assert mock_conn.fetch.called
    call_args = mock_conn.fetch.call_args[0]
    assert "users" in call_args


@pytest.mark.asyncio
async def test_describe_table_with_comments_uses_cache(mocker: MockerFixture) -> None:
    """Test that describe_table_with_comments uses cache on second call."""
    # Clear rate limit for this test
    from src.utils.validators import _LAST_CALL

    _LAST_CALL.clear()

    # Mock rate_limit to always return None
    mocker.patch("src.tools.schema.rate_limit", return_value=None)

    mock_conn = mocker.AsyncMock()
    mock_conn.fetchrow.return_value = {"table_comment": "Test"}
    mock_conn.fetch.return_value = [
        {
            "column_name": "id",
            "data_type": "integer",
            "is_nullable": False,
            "column_comment": "ID",
        }
    ]

    mock_ac = mocker.patch("src.tools.schema.async_connection")
    mock_ac.return_value.__aenter__.return_value = mock_conn
    mock_ac.return_value.__aexit__.return_value = None

    # Mock cache to return None first time, then return cached data
    cached_data = "Cached schema result"
    mocker.patch("src.tools.schema.get_cached_schema", side_effect=[None, cached_data])
    mocker.patch("src.tools.schema.set_cached_schema")

    # First call - should query database
    result1 = await describe_table_with_comments("test_db", "users")
    assert "Test" in result1 or "ID" in result1

    # Second call - should use cache
    result2 = await describe_table_with_comments("test_db", "users")
    assert cached_data in result2


@pytest.mark.asyncio
async def test_describe_table_with_invalid_identifier(mocker: MockerFixture) -> None:
    """Test describe_table with invalid table identifier."""
    result = await describe_table("test_db", "invalid-table-name")

    assert "error" in result.lower()


@pytest.mark.asyncio
async def test_describe_table_connection_error(mocker: MockerFixture) -> None:
    """Test describe_table when database connection fails."""
    mock_ac = mocker.patch("src.tools.schema.async_connection")
    mock_ac.return_value.__aenter__.side_effect = Exception("Connection failed")

    result = await describe_table("test_db", "users")

    assert "error" in result.lower()
