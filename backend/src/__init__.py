"""Root package for the backend API service.

This module provides the FastAPI backend that communicates with Redis
for task queueing and SSE streaming. Agent execution is handled by
the separate agent_service.
"""

from .config import QUESTION_PROPOSALS, settings

__all__ = [
    "settings",
    "QUESTION_PROPOSALS",
]
