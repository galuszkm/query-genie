"""Input sanitization and validation for user messages.

Provides protection against prompt injection, excessive input, and malicious content.
"""

import logging
import re
from typing import Final

logger = logging.getLogger(__name__)

# Maximum allowed message length (conservative limit)
MAX_MESSAGE_LENGTH: Final[int] = 10000

# Minimum meaningful message length
MIN_MESSAGE_LENGTH: Final[int] = 1

# Suspicious patterns that might indicate prompt injection attempts
# These are common prompt injection patterns but not definitive
SUSPICIOUS_PATTERNS: Final[list[tuple[str, str]]] = [
    # Direct instruction injection attempts
    (
        r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|commands?)",
        "instruction override",
    ),
    (r"(?i)disregard\s+(all\s+)?(previous|prior|above)", "instruction override"),
    (r"(?i)forget\s+(all\s+)?(previous|prior|above)", "instruction override"),
    # System prompt manipulation
    (
        r"(?i)(you\s+are\s+now|act\s+as|pretend\s+to\s+be|roleplay\s+as)\s+(?!.*\b(?:if|when|while)\b)",
        "role injection",
    ),
    (r"(?i)system\s*:\s*you\s+are", "system prompt injection"),
    # Delimiter confusion attempts
    (r"(?i)---+\s*end\s+of\s+(system|instructions?)", "delimiter injection"),
    (r"(?i)###\s*new\s+(system|instructions?)", "delimiter injection"),
    # Encoding/escaping attempts to bypass filters
    (r"\\x[0-9a-fA-F]{2}", "hex encoding"),
    (r"\\u[0-9a-fA-F]{4}", "unicode escape"),
    # Multiple special characters that might confuse parsing
    (r"[<>]{3,}", "excessive angle brackets"),
    (r"[{}]{3,}", "excessive braces"),
]

# Characters to strip/normalize
CONTROL_CHARS_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]"
)


class InputValidationError(ValueError):
    """Raised when input validation fails."""

    pass


def sanitize_message(message: str, strict: bool = True) -> str:
    """Sanitize and validate user message input.

    Args:
        message: Raw user input message
        strict: If True, reject messages with suspicious patterns.
                If False, only log warnings for suspicious patterns.

    Returns:
        Sanitized message string

    Raises:
        InputValidationError: If input fails validation
    """
    # Check length before any processing
    if len(message) > MAX_MESSAGE_LENGTH:
        raise InputValidationError(
            f"Message exceeds maximum length of {MAX_MESSAGE_LENGTH} characters "
            f"(got {len(message)})"
        )

    # Strip leading/trailing whitespace
    sanitized = message.strip()

    # Check minimum length
    if len(sanitized) < MIN_MESSAGE_LENGTH:
        raise InputValidationError("Message cannot be empty or only whitespace")

    # Remove control characters (except newlines and tabs)
    sanitized = CONTROL_CHARS_PATTERN.sub("", sanitized)

    # Check for suspicious patterns
    detected_patterns: list[str] = []
    for pattern, pattern_name in SUSPICIOUS_PATTERNS:
        if re.search(pattern, sanitized):
            detected_patterns.append(pattern_name)

    if detected_patterns:
        warning_msg = (
            f"Suspicious patterns detected in message: {', '.join(detected_patterns)}. "
            f"Message preview: {sanitized[:100]}..."
        )

        if strict:
            logger.warning(f"REJECTED: {warning_msg}")
            raise InputValidationError(
                "Message contains suspicious patterns that may indicate prompt injection attempts. "
                "Please rephrase your question."
            )
        else:
            # In non-strict mode, log but allow (monitoring for false positives)
            logger.warning(f"ALLOWED: {warning_msg}")

    # Normalize excessive whitespace
    sanitized = re.sub(r"\s+", " ", sanitized)

    # Final length check after processing
    if len(sanitized) > MAX_MESSAGE_LENGTH:
        raise InputValidationError(
            f"Message exceeds maximum length after sanitization: {MAX_MESSAGE_LENGTH}"
        )

    return sanitized


def validate_session_id(session_id: str | None) -> str | None:
    """Validate session ID format.

    Args:
        session_id: Session ID to validate

    Returns:
        Validated session ID or None

    Raises:
        InputValidationError: If session ID format is invalid
    """
    if session_id is None:
        return None

    # UUID v4 format
    uuid_pattern = re.compile(
        r"^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$",
        re.IGNORECASE,
    )

    if not uuid_pattern.match(session_id):
        raise InputValidationError(
            f"Invalid session ID format. Expected UUID v4, got: {session_id[:20]}..."
        )

    return session_id.lower()
