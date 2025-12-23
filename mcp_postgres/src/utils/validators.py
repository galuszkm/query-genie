"""Utility functions for MCP Postgres Server.

Provides helpers for rate limiting, identifier parsing/validation, and
query safety checks using SQL parsing.
"""

import logging
import re
import time

import sqlparse
from sqlparse.sql import Statement, Token
from sqlparse.tokens import DDL, DML, Keyword

from ..core.config import DANGEROUS_PATTERNS, settings

logger = logging.getLogger(__name__)
_LAST_CALL: dict[tuple[str, str], float] = {}


def rate_limit(tool_name: str, session_id: str | None = None) -> str | None:
    """Check if tool usage exceeds rate limit.

    Args:
        tool_name: Name of the tool being called.
        session_id: Session identifier for per-session rate limiting.

    Returns:
        Error message string if limit exceeded, else None.
    """
    # Create a composite key from tool_name and session_id
    # If no session_id, use a default key for global rate limiting
    key = (tool_name, session_id or "_global")

    now = time.monotonic()
    last = _LAST_CALL.get(key, 0)
    if now - last < settings.rate_limit_window:
        return "Rate limit exceeded. Please retry shortly."
    _LAST_CALL[key] = now
    return None


def parse_identifier(name: str) -> list[str]:
    """Parse optional schema-qualified identifier allowing mixed case; returns parts or raises."""
    parts = name.split(".")
    if not 1 <= len(parts) <= 2:
        raise ValueError("Only one or two-part identifiers are allowed")

    cleaned: list[str] = []
    for part in parts:
        # Strip double quotes to preserve case while still validating characters
        if part.startswith('"') and part.endswith('"') and len(part) >= 2:
            part = part[1:-1]
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", part):
            raise ValueError(f"Invalid identifier segment: {part!r}")
        cleaned.append(part)
    return cleaned


def format_qualified(parts: list[str]) -> str:
    """Quote each identifier part for safe schema-qualified usage."""
    return ".".join(f'"{p}"' for p in parts)


def validate_query(query_sql: str) -> str | None:
    """Validate query is safe using SQL parser.

    Uses sqlparse to properly parse SQL and detect dangerous operations,
    preventing bypasses that are possible with regex-based validation.

    Returns:
        Error message string if invalid, None if valid.
    """
    if not query_sql or not query_sql.strip():
        return "Error: Query cannot be empty."

    try:
        # Parse SQL into AST
        parsed = sqlparse.parse(query_sql)

        if not parsed:
            return "Error: Could not parse SQL query."

        # Check each statement in the query
        for statement in parsed:
            if not isinstance(statement, Statement):
                continue

            # Get the first meaningful token to determine statement type
            first_token: Token = statement.token_first(skip_ws=True, skip_cm=True)

            if not first_token:
                continue

            # Check if it's a SELECT statement
            if first_token.ttype is DML and first_token.value.upper() == "SELECT":
                # Valid SELECT, but check for dangerous operations in subqueries/CTEs
                error = _check_for_dangerous_keywords(statement)
                if error:
                    return error
            else:
                # Not a SELECT statement
                return f"Error: Only SELECT queries are allowed. Got: {first_token.value.upper()}"

        return None

    except Exception as e:
        logger.error(f"Error parsing SQL: {e}")
        return f"Error: Failed to parse SQL query: {str(e)}"


def _check_for_dangerous_keywords(statement: Statement) -> str | None:
    """Recursively check statement tokens for dangerous SQL keywords.

    Args:
        statement: Parsed SQL statement

    Returns:
        Error message if dangerous keyword found, None otherwise
    """

    def check_tokens(tokens: list[Token]) -> str | None:
        for token in tokens:
            # Check if token has subtokens (nested structure)
            if hasattr(token, "tokens"):
                error = check_tokens(token.tokens)
                if error:
                    return error

            # Check for DDL (Data Definition Language) keywords
            if token.ttype is DDL:
                return f"Error: Data modification keyword not allowed: {token.value.upper()}"

            # Check for DML keywords other than SELECT
            if token.ttype is DML and token.value.upper() != "SELECT":
                return f"Error: Data modification keyword not allowed: {token.value.upper()}"

            # Check for dangerous keywords as standalone keywords
            if token.ttype is Keyword:
                keyword_upper = token.value.upper()
                if keyword_upper in DANGEROUS_PATTERNS:
                    return f"Error: Forbidden keyword: {keyword_upper}"

        return None

    return check_tokens(statement.tokens)
