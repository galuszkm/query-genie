"""API module.

Provides FastAPI router and request/response models.
"""

from .models import ChatRequest, HealthResponse
from .routes import router

__all__ = [
    "router",
    "ChatRequest",
    "HealthResponse",
]
