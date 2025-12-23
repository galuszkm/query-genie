"""Database connection management.

Handles asyncpg connection pooling, context management for connections,
and statement timeout configuration.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any

import asyncpg

from .config import DATABASE_URLS, settings

logger = logging.getLogger("mcp_postgres")

# Async connection pools
_ASYNC_POOLS: dict[str, asyncpg.Pool] = {}
_ASYNC_POOLS_LOCK = asyncio.Lock()


async def get_async_pool(database: str) -> asyncpg.Pool:
    """Get or create async connection pool for the specified database."""
    if database not in DATABASE_URLS:
        available = ", ".join(DATABASE_URLS.keys())
        raise ValueError(
            f"Database '{database}' is not configured. "
            f"Available databases: {available}. "
        )

    async with _ASYNC_POOLS_LOCK:
        if database not in _ASYNC_POOLS:
            dsn = DATABASE_URLS[database]
            _ASYNC_POOLS[database] = await asyncpg.create_pool(
                dsn=dsn,
                min_size=settings.db_pool_min_size,
                max_size=settings.db_pool_size,
                command_timeout=settings.default_timeout_ms / 1000,
                max_inactive_connection_lifetime=settings.db_pool_idle_timeout,
            )
            logger.info(
                f"Async pool created for database: {database} "
                f"(min={settings.db_pool_min_size}, max={settings.db_pool_size}, "
                f"idle_timeout={settings.db_pool_idle_timeout}s)"
            )

    return _ASYNC_POOLS[database]


@asynccontextmanager
async def async_connection(database: str, timeout_ms: int | None = None) -> Any:
    """Async context manager for database connections with timeout support."""
    pool = await get_async_pool(database)

    # Clamp timeout to valid range
    effective_timeout = settings.default_timeout_ms
    if timeout_ms is not None:
        effective_timeout = max(1000, min(timeout_ms, settings.max_timeout_ms))

    async with pool.acquire() as conn:
        # Set statement timeout for this connection
        await conn.execute(f"SET statement_timeout TO {effective_timeout}")
        yield conn


async def close_pools() -> None:
    """Close all connection pools gracefully.

    Properly terminates all database connections before clearing the pool cache.
    This should be called during application shutdown to ensure clean resource cleanup.
    """
    async with _ASYNC_POOLS_LOCK:
        for db_name, pool in _ASYNC_POOLS.items():
            try:
                await pool.close()
                logger.info(f"Closed connection pool for database: {db_name}")
            except Exception as e:
                logger.error(f"Error closing pool for {db_name}: {e}")
        _ASYNC_POOLS.clear()
        logger.info("All connection pools closed")
