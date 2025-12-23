import asyncio
import logging
from typing import Any

from ..core.config import DATABASE_URLS
from ..core.database import async_connection

logger = logging.getLogger(__name__)


def list_databases() -> str:
    """List all configured databases available to query.

    Use this tool to find out which databases you can access.
    Returns a bulleted list of database names derived from environment variables.

    Returns:
        str: A Markdown-formatted list of available database names.

    Usage Tips:
        - Call this tool first to see what resources are available.
        - The returned names are required arguments for other tools.
    """
    logger.debug("list_databases called")

    if not DATABASE_URLS:
        logger.warning("No databases configured")
        return "No databases configured."

    logger.info(f"Listing {len(DATABASE_URLS)} configured databases")
    result = "Available databases (configured via environment):\n"
    for db_name in sorted(DATABASE_URLS.keys()):
        result += f"  • {db_name}\n"

    return result


async def list_all_tables() -> str:
    """List all tables across ALL configured databases.

    This is a comprehensive discovery tool to find data when you don't know which database to look in.

    Returns:
        str: A list of tables grouped by database, including table comments.
             Format:
             [database_name]
               • table_name - comment

    Usage Tips:
        - Use this for global search.
        - If you know the database, use `list_tables(database)` instead for speed.
    """
    logger.debug("list_all_tables called")

    if not DATABASE_URLS:
        logger.warning("No databases configured")
        return "No databases configured."

    async def fetch_tables_from_db(
        db_name: str,
    ) -> tuple[str, list[dict[str, Any]], str | None]:
        """Fetch tables from a single database asynchronously."""
        try:
            logger.debug(f"Fetching tables from database: {db_name}")
            async with async_connection(db_name) as conn:
                rows = await conn.fetch("""
                    SELECT
                        c.relname AS table_name,
                        obj_description(c.oid) AS table_comment
                    FROM pg_class c
                    WHERE c.relkind = 'r'
                    AND c.relnamespace = 'public'::regnamespace
                    ORDER BY c.relname
                """)
                tables = [
                    {
                        "database": db_name,
                        "table": row["table_name"],
                        "comment": row["table_comment"],
                    }
                    for row in rows
                ]
                logger.info(f"Found {len(tables)} tables in database: {db_name}")
                return db_name, tables, None
        except Exception as e:
            logger.error(f"Error accessing database '{db_name}': {e}", exc_info=True)
            return db_name, [], f"Error accessing database '{db_name}': {e}"

    # Fetch from all databases in parallel
    tasks = [fetch_tables_from_db(db_name) for db_name in sorted(DATABASE_URLS.keys())]
    results = await asyncio.gather(*tasks)

    all_tables = []
    errors = []
    for _db_name, tables, error in results:
        if error:
            errors.append(error)
        else:
            all_tables.extend(tables)

    if not all_tables and not errors:
        return "No tables found in any configured database."

    result = f"Tables across all databases ({len(all_tables)} total):\n\n"

    current_db = None
    for entry in all_tables:
        if current_db != entry["database"]:
            current_db = entry["database"]
            result += f"\n[{current_db}]\n"

        result += f"  • {entry['table']}"
        if entry["comment"]:
            result += f" - {entry['comment']}"
        result += "\n"

    if errors:
        result += "\n⚠️ Errors encountered:\n"
        for err in errors:
            result += f"  • {err}\n"

    return result


async def list_tables(database: str) -> str:
    """List all tables in the public schema of a specific database.

    Args:
        database (str): REQUIRED. The name of the database to query.

    Returns:
        str: A list of table names and their comments.

    Usage Tips:
        - Use this to explore a specific database found via `list_databases`.
        - Returns exact table names needed for other tools.
    """
    try:
        async with async_connection(database) as conn:
            tables = await conn.fetch("""
                SELECT
                    c.relname AS table_name,
                    obj_description(c.oid) AS table_comment
                FROM pg_class c
                WHERE c.relkind = 'r'
                AND c.relnamespace = 'public'::regnamespace
                ORDER BY c.relname
            """)

            if not tables:
                return f"No tables found in public schema of database '{database}'"

            result = f"Available tables in database '{database}':\n"
            for table in tables:
                result += f"  • {table['table_name']}"
                if table["table_comment"]:
                    result += f":  {table['table_comment']}"
                result += "\n"

            return result
    except Exception as e:
        return f"Error listing tables in database '{database}': {e}"
