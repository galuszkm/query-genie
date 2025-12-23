import logging

from ..core.database import async_connection
from ..utils.errors import database_error, validation_error
from ..utils.validators import (
    format_qualified,
    parse_identifier,
    validate_query,
)

logger = logging.getLogger(__name__)


async def query(
    database: str,
    query_sql: str,
    limit: int = 50,
    timeout_ms: int = 5000,
    compact: bool = False,
) -> str:
    """Execute a read-only SELECT query against a database.

    Args:
        database (str): REQUIRED. The name of the database to query.
        query_sql (str): REQUIRED. Valid SQL SELECT statement.
                         DML/DDL (INSERT, UPDATE, DELETE, etc.) are blocked.
        limit (int): Max rows to return. Default 50. Max 5000.
                     Adjust this if you need larger result sets.
        timeout_ms (int): Query timeout in ms. Default 5000. Max 30000.
        compact (bool): If True, returns compressed format (one JSON object per line).
                        Essential for reducing token usage with large datasets.

    Returns:
        str: Query results (text or compact format).

    Usage Tips:
        - Use this when standard tools (`list_tables`, `describe_table`) aren't specific enough.
        - Prefer `compact=True` for >50 rows.
    """
    logger.debug(
        f"query called: database={database}, limit={limit}, timeout_ms={timeout_ms}, compact={compact}"
    )

    # Input validation
    if not database or not isinstance(database, str):
        return validation_error(
            "database parameter is required and must be a string",
            parameter="database",
            received_type=type(database).__name__,
        )

    if not query_sql or not isinstance(query_sql, str):
        return validation_error(
            "query_sql parameter is required and must be a string",
            parameter="query_sql",
            received_type=type(query_sql).__name__,
        )

    if not query_sql.strip():
        return validation_error("query_sql cannot be empty", parameter="query_sql")

    if error := validate_query(query_sql):
        logger.warning(f"Query validation failed: {error}")
        return error

    # Clamp limit between 1 and 5000
    limit = max(1, min(limit, 5000))

    try:
        logger.info(
            f"Executing query on database '{database}' with timeout {timeout_ms}ms"
        )
        async with async_connection(database, timeout_ms=timeout_ms) as conn:
            rows = await conn.fetch(query_sql.strip())

            if not rows:
                logger.debug("Query returned no results")
                return "No results found."

            total_rows = len(rows)
            logger.info(
                f"Query returned {total_rows} rows, returning {min(limit, total_rows)}"
            )

            if compact:
                result = [str(dict(row)).replace("\n", " ") for row in rows[:limit]]
            else:
                result = [str(dict(row)) for row in rows[:limit]]

            if total_rows > limit:
                result.append(
                    f"... (showing {limit} of {total_rows} rows, increase 'limit' parameter if you need more)"
                )

            return "\n".join(result)
    except Exception as e:
        logger.error(f"Query error in database '{database}': {e}", exc_info=True)
        return database_error(str(e), database=database, operation="query")


async def get_row_count(database: str, table_name: str) -> str:
    """Get the total size of a table (row count).

    Args:
        database (str): REQUIRED. Database name.
        table_name (str): REQUIRED. Table name.

    Returns:
        str: Formatted count message.
    """
    logger.debug(f"get_row_count called: database={database}, table_name={table_name}")
    try:
        parts = parse_identifier(table_name)
    except ValueError as exc:
        logger.warning(f"Invalid table identifier '{table_name}': {exc}")
        return validation_error(str(exc), parameter="table_name", value=table_name)

    qualified = format_qualified(parts)

    try:
        async with async_connection(database) as conn:
            result = await conn.fetchval(f"SELECT COUNT(*) FROM {qualified}")
            if result is None:
                logger.error(
                    f"Could not get count for '{table_name}' in database '{database}'"
                )
                return database_error(
                    f"Could not get count for '{table_name}'",
                    database=database,
                    table=table_name,
                )
            logger.info(
                f"Table '{table_name}' in database '{database}' has {result} rows"
            )
            return f"Table '{table_name}' in database '{database}' has {result} rows."
    except Exception as e:
        logger.error(
            f"Error getting row count in database '{database}': {e}", exc_info=True
        )
        return database_error(str(e), database=database, table=table_name)


async def sample_data(database: str, table_name: str, limit: int = 5) -> str:
    """Preview actual data from a table.

    Args:
        database (str): REQUIRED. Database name.
        table_name (str): REQUIRED. Table name.
        limit (int): Number of rows. Default 5. Max 100.

    Returns:
        str: Sample rows formatted as dictionaries.

    Usage Tips:
        - Use this to understand the *content* and data formats of columns.
    """
    try:
        parts = parse_identifier(table_name)
    except ValueError as exc:
        return validation_error(str(exc), parameter="table_name", value=table_name)
    limit = max(1, min(limit, 100))

    qualified = format_qualified(parts)

    try:
        async with async_connection(database) as conn:
            rows = await conn.fetch(f"SELECT * FROM {qualified} LIMIT {limit}")
            if not rows:
                return f"No data in table '{table_name}' in database '{database}'."
            return "\n".join(str(dict(row)) for row in rows)
    except Exception as e:
        return database_error(str(e), database=database, table=table_name)


async def explain_query(database: str, query_sql: str) -> str:
    """Analyze query performance without executing it (EXPLAIN).

    Args:
        database (str): REQUIRED. Database name.
        query_sql (str): REQUIRED. The SELECT query to analyze.

    Returns:
        str: The Postgres query execution plan.
    """
    if error := validate_query(query_sql):
        return error

    try:
        async with async_connection(database) as conn:
            rows = await conn.fetch("EXPLAIN " + query_sql.strip())
            return "\n".join(row[0] for row in rows)
    except Exception as e:
        return database_error(str(e), database=database, operation="explain")
