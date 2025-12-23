"""Structured logging configuration for agent service.

Provides enhanced logging with request/session tracking.
"""

import logging
import sys
from contextvars import ContextVar

# Context variables for request tracking
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
session_id_var: ContextVar[str | None] = ContextVar("session_id", default=None)


class ContextFilter(logging.Filter):
    """Inject correlation IDs into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add request_id and session_id to log record."""
        record.request_id = request_id_var.get() or "-"
        record.session_id = session_id_var.get() or "-"
        return True


class StructuredFormatter(logging.Formatter):
    """JSON-like structured logging formatter."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with structured fields."""
        message = super().format(record)

        request_id = getattr(record, "request_id", "-")
        session_id = getattr(record, "session_id", "-")

        parts = [
            f"[{record.levelname}]",
            f"[{record.name}]",
        ]

        if request_id != "-":
            parts.append(f"[req:{request_id[:8]}]")
        if session_id != "-":
            parts.append(f"[sess:{session_id[:8]}]")

        parts.append(message)

        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            parts.append(f"\n{exc_text}")

        return " ".join(parts)


def configure_logging(level: str = "INFO") -> None:
    """Configure structured logging for the worker.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        StructuredFormatter("%(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    )
    handler.addFilter(ContextFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
