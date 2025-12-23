"""Centralized configuration for API and Redis connectivity."""

import logging
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings with validation and type safety."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment configuration
    environment: Literal["development", "production", "prod", "staging"] = Field(
        default="development", description="Deployment environment"
    )

    # Security / API configuration
    allowed_origins: str = Field(default="", description="Comma-separated CORS origins")
    api_key: SecretStr | None = Field(
        default=None, description="API authentication key"
    )
    input_sanitizer_strict: bool = Field(
        default=True, description="Enable strict input validation"
    )

    # Redis Configuration
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for task queue and pub/sub",
    )
    redis_task_queue: str = Field(
        default="agent:tasks", description="Redis list key for task queue"
    )

    # Session Configuration (for session details endpoint)
    sessions_dir: str = Field(
        default="strands_sessions", description="Directory for session storage"
    )

    def get_allowed_origins(self) -> list[str]:
        """Return allowed CORS origins - disabled in production, configurable in development.

        Production: CORS is completely disabled (empty list) for maximum security.
        Development: Uses allowed_origins if set, otherwise localhost defaults.

        Returns:
            List of allowed origin URLs (empty in production)
        """
        # Production: no CORS support at all
        is_production = self.environment in ("production", "prod", "staging")

        if is_production:
            logger.info(
                "Production mode: CORS is disabled (no cross-origin requests allowed)"
            )
            return []

        # Development: check env var first
        if self.allowed_origins:
            origins = [
                origin.strip()
                for origin in self.allowed_origins.split(",")
                if origin.strip()
            ]
            logger.info(
                f"Development mode: CORS enabled for {len(origins)} configured origins"
            )
            return origins

        # Development: default localhost origins
        default_origins = [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        ]
        logger.info(
            f"Development mode: CORS enabled for {len(default_origins)} default localhost origins"
        )
        return default_origins


# Initialize settings singleton (loads from .env and environment variables)
settings = Settings()


# Welcome screen configuration
WELCOME_CONFIG: dict[str, str] = {
    "title": "Welcome! Ask me anything related to your databases.",
    "subtitle": "Try questions like:",
}

# Question proposals for welcome screen
QUESTION_PROPOSALS: list[str] = [
    "What are the top 5 best-selling products by total revenue? Include product names, categories, and total sales.",
    "Which warehouse has the highest inventory value? Calculate the total value of products stored in each warehouse.",
    "Show me the average order value by country. Which country has the highest spending customers?",
    "Find products with the highest average rating (4.5 or above) that have at least 10 reviews. List them with their categories.",
    "Which manufacturer produces the most expensive products on average? Compare all manufacturers.",
    "What's the customer retention rate? How many customers placed more than one order in the last 90 days?",
    "Analyze order fulfillment speed: what's the average time between order date and delivery date by warehouse?",
    "Which product categories have the lowest stock levels relative to their sales volume? Identify potential stock-out risks.",
]
