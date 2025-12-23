import asyncio
import logging

from ..core.config import DATABASE_URLS
from ..core.database import async_connection

logger = logging.getLogger(__name__)


async def mcp_server_health() -> str:
    """Check MCP server health and connection status.

    Returns:
        str: Server health status including database connectivity.
    """
    try:
        db_count = len(DATABASE_URLS)
        db_names = ", ".join(DATABASE_URLS.keys())

        # Test one database connection to verify pool is working
        if DATABASE_URLS:
            first_db = next(iter(DATABASE_URLS.keys()))
            async with async_connection(first_db) as conn:
                await conn.fetchval("SELECT 1")

        return f"MCP Server: Healthy\nDatabases configured: {db_count} ({db_names})\nConnection pools: Active"
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return f"MCP Server: Degraded - {str(e)}"


async def database_health(database: str) -> str:
    """Monitor database status (size, cache ratio).

    Args:
        database (str): REQUIRED. The name of the database to check.

    Returns:
        str: Health metrics summary.
    """
    logger.debug(f"database_health called for: {database}")

    try:
        logger.info(f"Fetching health metrics for database: {database}")
        async with async_connection(database) as conn:
            checks = []

            size = await conn.fetchval(
                "SELECT pg_size_pretty(pg_database_size(current_database()))"
            )
            if size:
                checks.append(f"Database size: {size}")

            cache_ratio = await conn.fetchval("""
                SELECT round(100.0 * sum(blks_hit) /
                       nullif(sum(blks_hit + blks_read), 0), 2)
                FROM pg_stat_database WHERE datname = current_database()
            """)
            if cache_ratio is not None:
                checks.append(f"Cache hit ratio: {cache_ratio}%")

            logger.info(
                f"Health check completed for database '{database}': {len(checks)} metrics"
            )
            return "\n".join(checks)
    except Exception as e:
        logger.error(
            f"Error checking health for database '{database}': {e}", exc_info=True
        )
        return f"Error: {e}"


async def test_all_connections(max_retries: int = 30, retry_delay: int = 1) -> bool:
    """Test async database connections for all configured databases with retries.

    Args:
        max_retries: Maximum number of connection attempts per database.
        retry_delay: Delay in seconds between retry attempts.

    Returns:
        bool: True if all databases connected successfully, False otherwise.
    """
    if not DATABASE_URLS:
        logger.error("No databases configured. Cannot start server.")
        return False

    logger.info(f"Testing connections to {len(DATABASE_URLS)} database(s)...")

    failed_databases = []

    for db_name in DATABASE_URLS.keys():
        logger.info(f"Testing connection to database: {db_name}")

        for attempt in range(max_retries):
            try:
                async with async_connection(db_name) as conn:
                    version = await conn.fetchval("SELECT version()")
                    logger.info(f"✓ Connection to database '{db_name}' established.")
                    logger.info(
                        f"  PostgreSQL: {version.split(',')[0] if version else 'unknown'}"
                    )
                    break
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Database '{db_name}' not ready yet (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay}s..."
                    )
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(
                        f"✗ Failed to connect to database '{db_name}' after {max_retries} attempts: {e}"
                    )
                    failed_databases.append(db_name)
                    break

    if failed_databases:
        logger.error(
            f"Failed to connect to {len(failed_databases)} database(s): {', '.join(failed_databases)}"
        )
        logger.error(
            "Please check your DATABASE*_URL environment variables for typos or connectivity issues."
        )
        return False

    logger.info(
        f"✓ All {len(DATABASE_URLS)} database(s) connected successfully: {', '.join(DATABASE_URLS.keys())}"
    )
    return True
