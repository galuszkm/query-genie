"""Configuration management for MCP Postgres Server.

Handles environment variable loading, parsing of database connection strings,
and definition of global constants.
"""

import logging
import os
from urllib.parse import urlparse

from dotenv import load_dotenv
from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

logger = logging.getLogger("mcp_postgres")


class Settings(BaseSettings):
    """MCP Postgres server settings with validation and type safety."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Server Configuration
    mcp_server_host: str = Field(
        default="127.0.0.1", description="MCP server host address"
    )
    mcp_server_port: int = Field(
        default=8000, ge=1, le=65535, description="MCP server port"
    )

    # Timeout Configuration
    default_timeout_ms: int = Field(
        default=5000, ge=1000, description="Default query timeout in milliseconds"
    )
    max_timeout_ms: int = Field(
        default=30000, ge=1000, description="Maximum query timeout in milliseconds"
    )

    # Connection Pool Settings
    db_pool_size: int = Field(default=20, ge=1, description="Max pool connections")
    db_pool_min_size: int = Field(default=5, ge=1, description="Min pool connections")
    db_pool_idle_timeout: int = Field(
        default=300, ge=0, description="Idle connection timeout in seconds"
    )

    # Rate Limiting
    rate_limit_window: float = Field(
        default=0.01, ge=0.0, description="Minimum seconds between calls"
    )

    @field_validator("db_pool_min_size")
    @classmethod
    def validate_pool_sizes(cls, v: int, info: ValidationInfo) -> int:
        """Ensure min_size <= max_size."""
        data = info.data
        if "db_pool_size" in data and v > data["db_pool_size"]:
            raise ValueError("db_pool_min_size cannot exceed db_pool_size")
        return v

    @field_validator("max_timeout_ms")
    @classmethod
    def validate_max_timeout(cls, v: int, info: ValidationInfo) -> int:
        """Ensure max_timeout >= default_timeout."""
        data = info.data
        if "default_timeout_ms" in data and v < data["default_timeout_ms"]:
            raise ValueError("max_timeout_ms must be >= default_timeout_ms")
        return v


# Initialize settings singleton
settings = Settings()

# Dangerous SQL patterns to block (frozen for immutability)
DANGEROUS_PATTERNS = frozenset(
    [
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "TRUNCATE",
        "ALTER",
        "CREATE",
        "GRANT",
        "REVOKE",
        "EXECUTE",
    ]
)


def load_database_urls() -> dict[str, str]:
    """Load all DATABASE*_URL environment variables."""
    db_urls = {}
    for key, value in os.environ.items():
        if key.startswith("DATABASE") and key.endswith("_URL") and value:
            # Extract database name from connection string
            try:
                parsed = urlparse(value)
                db_name = parsed.path.lstrip("/")
                if db_name:
                    db_urls[db_name] = value
                    logger.info(f"Loaded configuration for database: {db_name}")
            except Exception as e:
                logger.warning(f"Failed to parse {key}: {e}")

    if not db_urls:
        logger.warning("No DATABASE*_URL environment variables found.")

    return db_urls


# Initialize global config
DATABASE_URLS = load_database_urls()
