"""Core infrastructure modules for MCP Postgres Server.

Contains configuration, database connections, and caching.
"""

from .cache import (
    SCHEMA_CACHE_TTL,
    get_cached_schema,
    set_cached_schema,
)
from .config import (
    DANGEROUS_PATTERNS,
    DATABASE_URLS,
    load_database_urls,
    settings,
)
from .database import (
    async_connection,
    close_pools,
    get_async_pool,
)

__all__ = [
    # Config
    "settings",
    "DANGEROUS_PATTERNS",
    "DATABASE_URLS",
    "load_database_urls",
    # Database
    "get_async_pool",
    "async_connection",
    "close_pools",
    # Cache
    "get_cached_schema",
    "set_cached_schema",
    "SCHEMA_CACHE_TTL",
]
