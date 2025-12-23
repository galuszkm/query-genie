"""Tests for discovery tools."""

import pytest
from pytest_mock import MockerFixture

from src.tools.discovery import (
    list_all_tables,
    list_databases,
    list_tables,
)

# Mock data
MOCK_DBS = {"test_db": "postgres://user:pass@localhost/test_db"}
MOCK_TABLES = [
    {"table_name": "users", "table_comment": "User accounts"},
    {"table_name": "posts", "table_comment": None},
]


def test_list_databases_success(mocker: MockerFixture) -> None:
    """Test listing databases when configured."""
    mocker.patch("src.tools.discovery.DATABASE_URLS", MOCK_DBS)
    result = list_databases()
    assert "test_db" in result
    assert "Available databases" in result


def test_list_databases_empty(mocker: MockerFixture) -> None:
    """Test listing databases when none configured."""
    mocker.patch("src.tools.discovery.DATABASE_URLS", {})
    result = list_databases()
    assert "No databases configured" in result


@pytest.mark.asyncio
async def test_list_tables_success(mocker: MockerFixture) -> None:
    """Test listing tables for a specific database."""
    mock_conn = mocker.AsyncMock()
    mock_conn.fetch.return_value = MOCK_TABLES

    mock_ac = mocker.patch("src.tools.discovery.async_connection")
    mock_ac.return_value.__aenter__ = mocker.AsyncMock(return_value=mock_conn)
    mock_ac.return_value.__aexit__ = mocker.AsyncMock(return_value=None)

    result = await list_tables("test_db")

    assert "users" in result
    assert "User accounts" in result
    assert "posts" in result
    assert "Available tables in database 'test_db'" in result


@pytest.mark.asyncio
async def test_list_tables_error(mocker: MockerFixture) -> None:
    """Test error handling during table listing."""
    mock_ac = mocker.patch("src.tools.discovery.async_connection")
    # Simulate connection error
    mock_ac.return_value.__aenter__.side_effect = Exception("Connection failed")

    result = await list_tables("test_db")
    assert "Error listing tables" in result
    assert "Connection failed" in result


@pytest.mark.asyncio
async def test_list_all_tables(mocker: MockerFixture) -> None:
    """Test cross-database table listing."""
    mock_conn = mocker.AsyncMock()
    mock_conn.fetch.return_value = MOCK_TABLES

    mocker.patch("src.tools.discovery.DATABASE_URLS", MOCK_DBS)
    mock_ac = mocker.patch("src.tools.discovery.async_connection")
    mock_ac.return_value.__aenter__ = mocker.AsyncMock(return_value=mock_conn)
    mock_ac.return_value.__aexit__ = mocker.AsyncMock(return_value=None)

    result = await list_all_tables()

    # Check output structure
    assert "[test_db]" in result
    assert "users" in result
