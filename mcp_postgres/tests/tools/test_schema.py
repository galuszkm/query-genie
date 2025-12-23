"""Tests for schema tools."""

from typing import Any

import pytest
from pytest_mock import MockerFixture

from src.tools.schema import (
    describe_table,
    describe_table_with_comments,
    get_query_syntax_help,
    get_table_comments,
    list_foreign_keys,
    list_indexes,
)

# Mock data
MOCK_COLUMNS_SIMPLE = [
    {
        "column_name": "id",
        "data_type": "integer",
        "is_nullable": "NO",
        "column_default": "nextval('users_id_seq')",
    },
    {
        "column_name": "name",
        "data_type": "text",
        "is_nullable": "YES",
        "column_default": None,
    },
]

MOCK_COLUMNS_RICH = [
    {
        "column_name": "id",
        "data_type": "integer",
        "is_nullable": False,
        "column_comment": "PK",
    },
    {
        "column_name": "name",
        "data_type": "text",
        "is_nullable": True,
        "column_comment": "User full name",
    },
]


@pytest.fixture
def mock_db_connection(mocker: MockerFixture) -> Any:
    """Fixture for mocked database connection."""
    mock_conn = mocker.AsyncMock()
    mock_ac = mocker.patch("src.tools.schema.async_connection")
    mock_ac.return_value.__aenter__.return_value = mock_conn
    mock_ac.return_value.__aexit__.return_value = None
    return mock_conn


@pytest.mark.asyncio
async def test_describe_table(mock_db_connection: Any) -> None:
    """Test basic table description."""
    mock_db_connection.fetch.return_value = MOCK_COLUMNS_SIMPLE

    result = await describe_table("test_db", "users")

    assert "id: integer (NOT NULL DEFAULT nextval('users_id_seq'))" in result
    assert "name: text (NULL)" in result
    assert "Schema for 'users' in database 'test_db'" in result


@pytest.mark.asyncio
async def test_describe_table_with_comments(
    mock_db_connection: Any, mocker: MockerFixture
) -> None:
    """Test table description with comments and caching."""
    # Mocking fetchrow for table comment and fetch for columns
    mock_db_connection.fetchrow.return_value = {"table_comment": "User table"}
    mock_db_connection.fetch.return_value = MOCK_COLUMNS_RICH

    # Mock cache functions
    mocker.patch("src.tools.schema.get_cached_schema", return_value=None)
    mock_set_cache = mocker.patch("src.tools.schema.set_cached_schema")

    result = await describe_table_with_comments("test_db", "users")

    assert "Table: users" in result
    assert "Description: User table" in result
    assert "id (integer) NOT NULL" in result
    assert "→ PK" in result

    mock_set_cache.assert_called_once()


@pytest.mark.asyncio
async def test_get_query_syntax_help(mock_db_connection: Any) -> None:
    """Test query syntax help for case-sensitive identifiers."""
    mock_db_connection.fetch.return_value = [
        {"column_name": "Id"},
        {"column_name": "User Name"},
    ]

    result = await get_query_syntax_help("test_db", "UseRs")

    assert 'SELECT "Id", "User Name" FROM "UseRs"' in result
    assert "CRITICAL RULE" in result


@pytest.mark.asyncio
async def test_list_indexes(mock_db_connection: Any) -> None:
    """Test listing table indexes."""
    mock_db_connection.fetch.return_value = [
        {
            "indexname": "users_pkey",
            "indexdef": "CREATE UNIQUE INDEX users_pkey ON public.users USING btree (id)",
        }
    ]

    result = await list_indexes("test_db", "users")

    assert "users_pkey" in result
    assert "CREATE UNIQUE INDEX" in result


@pytest.mark.asyncio
async def test_list_foreign_keys(mock_db_connection: Any) -> None:
    """Test listing table foreign keys."""
    mock_db_connection.fetch.return_value = [
        {
            "conname": "users_org_id_fkey",
            "pg_get_constraintdef": "FOREIGN KEY (org_id) REFERENCES orgs(id)",
        }
    ]

    result = await list_foreign_keys("test_db", "users")

    assert "users_org_id_fkey" in result
    assert "FOREIGN KEY (org_id)" in result


@pytest.mark.asyncio
async def test_get_table_comments(mock_db_connection: Any) -> None:
    """Test getting table and column comments."""
    mock_db_connection.fetchval.return_value = "Table comment"
    mock_db_connection.fetch.return_value = [
        {"attname": "col1", "col_description": "Col comment"}
    ]

    result = await get_table_comments("test_db", "users")

    assert "Table 'users' in database 'test_db': Table comment" in result
    assert "col1: Col comment" in result
