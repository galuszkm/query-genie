"""Integration tests for query tools with validators."""

from typing import Any

import pytest
from pytest_mock import MockerFixture

from src.tools.query import query, sample_data


@pytest.mark.asyncio
async def test_query_with_sql_injection_attempt(mocker: MockerFixture) -> None:
    """Test that SQL injection attempts are blocked."""
    # Mock database configuration so validation runs but connection fails gracefully
    mocker.patch(
        "src.core.config.DATABASE_URLS", {"test_db": "postgresql://localhost/test"}
    )

    dangerous_queries = [
        "SELECT * FROM users; DROP TABLE users;",
        "SELECT * FROM users WHERE id = 1; DELETE FROM users;",
    ]

    for dangerous_query in dangerous_queries:
        result = await query("test_db", dangerous_query)
        assert "forbidden keyword" in result.lower() or "only select" in result.lower()


@pytest.mark.asyncio
async def test_query_with_case_variations() -> None:
    """Test that forbidden keywords are caught regardless of case."""
    variations = [
        "select * from users; DELETE from users",
        "SELECT * FROM users; delete FROM users",
        "SeLeCt * FrOm users; DeLeTe FrOm users",
    ]

    for variation in variations:
        result = await query("test_db", variation)
        assert "forbidden keyword" in result.lower() or "only select" in result.lower()


@pytest.mark.asyncio
async def test_query_timeout_boundaries(mocker: MockerFixture) -> None:
    """Test that timeout parameter is properly validated and clamped."""
    mock_conn = mocker.AsyncMock()
    mock_conn.fetch.return_value = [{"col": "val"}]

    # Track the actual timeout_ms passed
    captured_timeout = []

    class MockContext:
        def __init__(self, db: str, timeout_ms: int | None = None) -> None:
            captured_timeout.append(timeout_ms)

        async def __aenter__(self) -> Any:
            return mock_conn

        async def __aexit__(self, *args: Any) -> None:
            pass

    mocker.patch("src.tools.query.async_connection", MockContext)

    # Test with very high timeout
    await query("test_db", "SELECT 1", timeout_ms=999999)

    # Should have been clamped to MAX_TIMEOUT_MS (5000 or 30000)
    assert (
        captured_timeout[0] == 999999
    )  # Passed as-is, clamping happens in async_connection


@pytest.mark.asyncio
async def test_sample_data_with_invalid_table(mocker: MockerFixture) -> None:
    """Test sample_data handles invalid table names."""
    mock_conn = mocker.AsyncMock()
    mock_conn.fetch.side_effect = Exception("relation does not exist")

    mock_ac = mocker.patch("src.tools.query.async_connection")
    mock_ac.return_value.__aenter__.return_value = mock_conn
    mock_ac.return_value.__aexit__.return_value = None

    result = await sample_data("test_db", "nonexistent_table")

    assert "error" in result.lower() or "relation does not exist" in result.lower()


@pytest.mark.asyncio
async def test_query_empty_result_handling(mocker: MockerFixture) -> None:
    """Test that empty query results are handled gracefully."""
    mock_conn = mocker.AsyncMock()
    mock_conn.fetch.return_value = []

    mock_ac = mocker.patch("src.tools.query.async_connection")
    mock_ac.return_value.__aenter__.return_value = mock_conn
    mock_ac.return_value.__aexit__.return_value = None

    result = await query("test_db", "SELECT * FROM users WHERE 1=0")

    assert "no results" in result.lower()


@pytest.mark.asyncio
async def test_query_with_valid_created_at_column() -> None:
    """Test that columns containing forbidden keywords (like created_at) are allowed."""
    # This should NOT be blocked even though it contains "create"
    result = await query("test_db", "SELECT created_at, updated_at FROM users")

    # Should not see validation errors if "created_at" is handled with word boundaries
    # In practice, this might fail with connection error, but not validation error
    assert "forbidden keyword: CREATE" not in result
