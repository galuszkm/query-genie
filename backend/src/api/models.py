"""API models using Pydantic.

Request and response models for the chat API.
"""

from pydantic import BaseModel, Field, field_validator

from ..config import settings
from ..utils.input_sanitizer import sanitize_message


class ChatRequest(BaseModel):
    """Chat request model with validation.

    Attributes:
        message: User message to send to the agent
        stream: Enable streaming responses (always True for worker mode)
        session_id: Optional session ID for conversation continuity
    """

    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="User message to send to the agent",
    )
    stream: bool = Field(True, description="Enable streaming responses")
    session_id: str | None = Field(
        None, description="Optional session ID for conversation continuity"
    )

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Sanitize and validate message for security.

        Args:
            v: Raw message string

        Returns:
            Sanitized message string
        """
        # Use input sanitizer - strict mode based on config
        # Non-strict: logs warnings but allows potentially suspicious messages
        # Strict: rejects messages with suspicious patterns
        return sanitize_message(v, strict=settings.input_sanitizer_strict)


class HealthResponse(BaseModel):
    """Health check response model.

    Attributes:
        status: Overall health status: 'healthy' or 'degraded'
        redis_status: Redis connectivity status for worker communication
    """

    status: str = Field(
        ..., description="Overall health status: 'healthy' or 'degraded'"
    )
    redis_status: str = Field(
        default="skipped", description="Redis connectivity status for worker mode"
    )
