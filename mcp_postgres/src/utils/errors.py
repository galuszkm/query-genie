"""Error models for MCP tools."""

from typing import Any


class MCPError:
    """Structured error response for MCP tools.

    Returns a consistent error format that can be easily parsed
    by the LLM and logged for debugging.
    """

    def __init__(
        self, error_type: str, message: str, details: dict[str, Any] | None = None
    ) -> None:
        """Initialize MCP error.

        Args:
            error_type: Category of error (validation, database, timeout, etc.)
            message: Human-readable error message
            details: Optional additional context
        """
        self.error_type = error_type
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        """Format error as string for LLM consumption."""
        error_str = f"Error ({self.error_type}): {self.message}"
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            error_str += f" | Details: {details_str}"
        return error_str


def validation_error(message: str, **details: Any) -> str:
    """Create a validation error response.

    Args:
        message: Error description
        **details: Additional context (parameter name, expected type, etc.)

    Returns:
        Formatted error string
    """
    return str(MCPError("validation", message, details))


def database_error(message: str, **details: Any) -> str:
    """Create a database error response.

    Args:
        message: Error description
        **details: Additional context (database name, query snippet, etc.)

    Returns:
        Formatted error string
    """
    return str(MCPError("database", message, details))


def timeout_error(message: str, **details: Any) -> str:
    """Create a timeout error response.

    Args:
        message: Error description
        **details: Additional context (timeout value, operation, etc.)

    Returns:
        Formatted error string
    """
    return str(MCPError("timeout", message, details))


def rate_limit_error(message: str, **details: Any) -> str:
    """Create a rate limit error response.

    Args:
        message: Error description
        **details: Additional context (limit, window, etc.)

    Returns:
        Formatted error string
    """
    return str(MCPError("rate_limit", message, details))
