"""Tests for validator utilities."""

import pytest

from src.utils.validators import (
    format_qualified,
    parse_identifier,
    rate_limit,
    validate_query,
)


def test_parse_identifier_simple() -> None:
    """Test standard identifier parsing."""
    assert parse_identifier("users") == ["users"]
    assert parse_identifier("public.users") == ["public", "users"]


def test_parse_identifier_quoted() -> None:
    """Test quoted identifier parsing and stripping."""
    assert parse_identifier('"Users"') == ["Users"]
    assert parse_identifier('"public"."Users"') == ["public", "Users"]


def test_parse_identifier_mixed() -> None:
    """Test mixed quoted and unquoted."""
    assert parse_identifier('public."Users"') == ["public", "Users"]


def test_parse_identifier_invalid() -> None:
    """Test invalid identifiers."""
    with pytest.raises(ValueError):
        parse_identifier("schema.table.column")  # Too many parts
    with pytest.raises(ValueError):
        parse_identifier("invalid-char")
    with pytest.raises(ValueError):
        parse_identifier('"unclosed')


def test_format_qualified() -> None:
    """Test identifier quoting for SQL."""
    assert format_qualified(["users"]) == '"users"'
    assert format_qualified(["public", "users"]) == '"public"."users"'
    assert format_qualified(["Users"]) == '"Users"'


def test_validate_query_safe() -> None:
    """Test valid SELECT queries."""
    assert validate_query("SELECT * FROM users") is None
    assert validate_query("select id, name from public.users") is None
    assert validate_query("SELECT count(*) FROM users") is None
    # "created_at" contains "create" but should be safe due to boundaries
    assert validate_query("SELECT created_at FROM users") is None


def test_validate_query_unsafe() -> None:
    """Test forbidden keywords."""
    # Test SELECT checks
    result1 = validate_query("SELECT * FROM users; DELETE FROM users")
    assert result1 is not None and (
        "forbidden keyword: DELETE" in result1
        or "Only SELECT queries are allowed" in result1
    )

    result2 = validate_query("SELECT * FROM users; DROP TABLE users")
    assert result2 is not None and (
        "forbidden keyword: DROP" in result2
        or "Only SELECT queries are allowed" in result2
    )

    result3 = validate_query("SELECT * FROM users; INSERT INTO users VALUES (1)")
    assert result3 is not None and (
        "forbidden keyword: INSERT" in result3
        or "Only SELECT queries are allowed" in result3
    )

    # Test non-SELECT check
    result4 = validate_query("UPDATE users SET name='x'")
    assert result4 is not None and "Only SELECT queries are allowed" in result4

    result5 = validate_query("DELETE FROM users")
    assert result5 is not None and "Only SELECT queries are allowed" in result5


def test_rate_limit() -> None:
    """Test rate limiting logic."""
    # First call should pass
    assert rate_limit("test_tool") is None
    # Immediate second call should fail
    result = rate_limit("test_tool")
    assert result is not None and "Rate limit exceeded" in result
