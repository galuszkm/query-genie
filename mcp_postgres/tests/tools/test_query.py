"""Tests for query tools."""

from typing import Any

import pytest
from pytest_mock import MockerFixture

from src.tools.query import (
    explain_query,
    get_row_count,
    query,
    sample_data,
)


@pytest.fixture
def mock_db_connection(mocker: MockerFixture) -> Any:
    """Fixture for mocked database connection."""
    mock_conn = mocker.AsyncMock()
    mock_ac = mocker.patch("src.tools.query.async_connection")
    mock_ac.return_value.__aenter__.return_value = mock_conn
    mock_ac.return_value.__aexit__.return_value = None
    return mock_conn


@pytest.mark.asyncio
async def test_query_success(mock_db_connection: Any) -> None:
    """Test successful query execution."""
    mock_db_connection.fetch.return_value = [{"col1": "val1"}, {"col1": "val2"}]

    result = await query("test_db", "SELECT * FROM t")

    assert "{'col1': 'val1'}" in result
    assert "{'col1': 'val2'}" in result
    # Should not show truncation message
    assert "showing" not in result


@pytest.mark.asyncio
async def test_query_compact(mock_db_connection: Any) -> None:
    """Test compact query format."""
    mock_db_connection.fetch.return_value = [{"col1": "val1"}, {"col1": "val2"}]

    result = await query("test_db", "SELECT * FROM t", compact=True)

    # Compact format has no newlines within a row representation
    lines = result.split("\n")
    assert len(lines) == 2
    assert "{'col1': 'val1'}" in lines[0]


@pytest.mark.asyncio
async def test_query_limit_truncation(mock_db_connection: Any) -> None:
    """Test query result truncation with limit."""
    # Simulate returning more rows than limit
    mock_db_connection.fetch.return_value = [{"c": i} for i in range(55)]

    result = await query("test_db", "SELECT * FROM t", limit=50)

    assert "showing 50 of 55 rows" in result


@pytest.mark.asyncio
async def test_query_invalid_sql() -> None:
    """Test query validation for forbidden SQL."""
    # Attempt DDL
    result = await query("test_db", "DROP TABLE users")
    assert "Forbidden keyword" in result or "Only SELECT" in result


@pytest.mark.asyncio
async def test_get_row_count(mock_db_connection: Any) -> None:
    """Test getting row count for a table."""
    mock_db_connection.fetchval.return_value = 1234

    result = await get_row_count("test_db", "users")

    assert "has 1234 rows" in result


@pytest.mark.asyncio
async def test_sample_data(mock_db_connection: Any) -> None:
    """Test sampling table data."""
    mock_db_connection.fetch.return_value = [{"id": 1, "name": "Alice"}]

    result = await sample_data("test_db", "users", limit=1)

    assert "{'id': 1, 'name': 'Alice'}" in result


@pytest.mark.asyncio
async def test_explain_query(mock_db_connection: Any) -> None:
    """Test query execution plan explanation."""
    mock_db_connection.fetch.return_value = [("Seq Scan on users",), ("  Filter: ...",)]

    result = await explain_query("test_db", "SELECT * FROM users")

    assert "Seq Scan" in result
