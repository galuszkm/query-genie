import logging

from ..core.cache import get_cached_schema, set_cached_schema
from ..core.database import async_connection
from ..utils.errors import database_error, validation_error
from ..utils.validators import format_qualified, parse_identifier

logger = logging.getLogger(__name__)


async def describe_table(database: str, table_name: str) -> str:
    """Get basic column definitions (types, nullability, defaults) for a table.

    Args:
        database (str): REQUIRED. The name of the database containing the table.
        table_name (str): REQUIRED. The name of the table to describe.
                          Supports schema-qualified names (e.g., 'public.users').

    Returns:
        str: A formatted list of columns with their data types, nullable status, and default values.

    Usage Tips:
        - Use this for a quick schema overview.
        - For semantic context (comments), use `describe_table_with_comments` instead.
    """
    logger.debug(f"describe_table called: database={database}, table_name={table_name}")
    try:
        parts = parse_identifier(table_name)
    except ValueError as exc:
        logger.warning(f"Invalid table identifier '{table_name}': {exc}")
        return validation_error(str(exc), parameter="table_name", value=table_name)

    schema = parts[0] if len(parts) == 2 else "public"
    tbl = parts[-1]

    try:
        async with async_connection(database) as conn:
            columns = await conn.fetch(
                """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = $1 AND table_schema = $2
                ORDER BY ordinal_position
                """,
                tbl,
                schema,
            )
            if not columns:
                logger.warning(
                    f"Table '{table_name}' not found in database '{database}'"
                )
                return f"Table '{table_name}' not found in database '{database}'"

            logger.info(
                f"Retrieved schema for table '{table_name}' with {len(columns)} columns"
            )
            result = f"Schema for '{table_name}' in database '{database}':\n"
            for col in columns:
                nullable = "NULL" if col["is_nullable"] == "YES" else "NOT NULL"
                default = (
                    f" DEFAULT {col['column_default']}" if col["column_default"] else ""
                )
                result += f"  - {col['column_name']}: {col['data_type']} ({nullable}{default})\n"
            return result
    except Exception as e:
        logger.error(
            f"Error describing table '{table_name}' in database '{database}': {e}",
            exc_info=True,
        )
        return database_error(str(e), database=database, table=table_name)


async def describe_table_with_comments(database: str, table_name: str) -> str:
    """Get rich table metadata showing columns, types, and human-readable comments.

    This tool is essential for understanding the *meaning* of data, not just its structure.
    Results are cached for performance.

    Args:
        database (str): REQUIRED. The name of the database.
        table_name (str): REQUIRED. The table name.

    Returns:
        str: Detailed schema information including table description and column comments.
    """
    if cached := get_cached_schema(database, table_name):
        return f"(cached) {cached}"

    try:
        parts = parse_identifier(table_name)
    except ValueError as exc:
        return validation_error(str(exc), parameter="table_name", value=table_name)

    schema = parts[0] if len(parts) == 2 else "public"
    tbl = parts[-1]

    try:
        async with async_connection(database) as conn:
            # Get table comment
            table_info = await conn.fetchrow(
                """
                SELECT obj_description(oid) as table_comment
                FROM pg_class
                WHERE relname = $1 AND relnamespace = $2::regnamespace
                """,
                tbl,
                schema,
            )
            table_comment = table_info["table_comment"] if table_info else None

            # Get column details with comments
            columns = await conn.fetch(
                """
                SELECT
                    a.attname AS column_name,
                    pg_catalog.format_type(a.atttypid, a.atttypmod) AS data_type,
                    NOT a.attnotnull AS is_nullable,
                    pg_catalog.col_description(a.attrelid, a.attnum) AS column_comment
                FROM pg_catalog.pg_attribute a
                JOIN pg_catalog.pg_class c ON a.attrelid = c.oid
                WHERE c.relname = $1
                AND a.attnum > 0
                AND NOT a.attisdropped
                AND c.relnamespace = $2::regnamespace
                ORDER BY a.attnum
                """,
                tbl,
                schema,
            )

            if not columns:
                return f"Table '{table_name}' not found in {schema} schema of database '{database}'"

            result = f"Table: {table_name} (database: {database})\n"
            if table_comment:
                result += f"Description: {table_comment}\n"
            result += "\nColumns:\n"

            for col in columns:
                result += f"  - {col['column_name']} ({col['data_type']})"
                result += f" {'NULL' if col['is_nullable'] else 'NOT NULL'}"
                if col["column_comment"]:
                    result += f"\n    → {col['column_comment']}"
                result += "\n"

            set_cached_schema(database, table_name, result)
            return result
    except Exception as e:
        return database_error(str(e), database=database, table=table_name)


async def get_query_syntax_help(database: str, table_name: str) -> str:
    """Get correct SQL syntax examples for a specific table.

    Crucial for tables with mixed-case identifiers or reserved words.

    Args:
        database (str): REQUIRED. Database name.
        table_name (str): REQUIRED. Table name.

    Returns:
        str: Example SQL queries showing how to properly quote identifiers.
    """
    try:
        parts = parse_identifier(table_name)
    except ValueError as exc:
        return validation_error(str(exc), parameter="table_name", value=table_name)

    schema = parts[0] if len(parts) == 2 else "public"
    tbl = parts[-1]

    try:
        async with async_connection(database) as conn:
            columns = await conn.fetch(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = $1 AND table_schema = $2
                ORDER BY ordinal_position
                """,
                tbl,
                schema,
            )

            if not columns:
                return f"Table '{table_name}' not found in database '{database}'"

            quoted_table = f'"{table_name}"'
            quoted_cols = [f'"{col["column_name"]}"' for col in columns]

            result = f"🔧 SQL SYNTAX HELP for table '{table_name}' in database '{database}'\n\n"
            result += "CRITICAL RULE: Always quote identifiers with mixed case or special characters!\n\n"
            result += "✅ CORRECT SYNTAX EXAMPLES:\n\n"
            result += "1. SELECT specific columns:\n"
            result += f"   SELECT {', '.join(quoted_cols[:3])} FROM {quoted_table}\n\n"
            result += "2. SELECT all with WHERE:\n"
            result += (
                f"   SELECT * FROM {quoted_table} WHERE {quoted_cols[0]} = 'value'\n\n"
            )
            result += "3. COUNT and GROUP BY:\n"
            result += f"   SELECT {quoted_cols[0]}, COUNT(*) FROM {quoted_table} GROUP BY {quoted_cols[0]}\n\n"

            result += "📋 ALL COLUMNS (copy-paste ready):\n"
            for col in columns:
                result += f'   "{col["column_name"]}"\n'

            return result

    except Exception as e:
        return database_error(str(e), database=database, table=table_name)


async def list_indexes(database: str, table_name: str) -> str:
    """List indexes on a table to understand performance characteristics.

    Args:
        database (str): REQUIRED. Database name.
        table_name (str): REQUIRED. Table name.

    Returns:
        str: List of index names and definitions (SQL).
    """
    try:
        parts = parse_identifier(table_name)
    except ValueError as exc:
        return validation_error(str(exc), parameter="table_name", value=table_name)
    schema = parts[0] if len(parts) == 2 else "public"
    tbl = parts[-1]

    try:
        async with async_connection(database) as conn:
            indexes = await conn.fetch(
                """
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = $1 AND schemaname = $2
                ORDER BY indexname
                """,
                tbl,
                schema,
            )
            if not indexes:
                return f"No indexes on '{table_name}' in database '{database}'."
            result = f"Indexes on '{table_name}' in database '{database}':\n"
            for idx in indexes:
                result += f"  - {idx['indexname']}: {idx['indexdef']}\n"
            return result
    except Exception as e:
        return database_error(str(e), database=database, table=table_name)


async def list_foreign_keys(database: str, table_name: str) -> str:
    """List foreign key constraints to understand table relationships.

    Args:
        database (str): REQUIRED. Database name.
        table_name (str): REQUIRED. Table name.

    Returns:
        str: List of foreign keys and their constraint definitions.
    """
    try:
        parts = parse_identifier(table_name)
    except ValueError as exc:
        return validation_error(str(exc), parameter="table_name", value=table_name)
    qualified = format_qualified(parts)

    try:
        async with async_connection(database) as conn:
            fks = await conn.fetch(
                f"""
                SELECT conname, pg_catalog.pg_get_constraintdef(r.oid, TRUE)
                FROM pg_catalog.pg_constraint r
                WHERE r.conrelid = '{qualified}'::regclass AND r.contype = 'f'
                ORDER BY conname
                """
            )
            if not fks:
                return f"No foreign keys on '{table_name}' in database '{database}'."
            result = f"Foreign keys on '{table_name}' in database '{database}':\n"
            for fk in fks:
                result += f"  - {fk['conname']}: {fk['pg_get_constraintdef']}\n"
            return result
    except Exception as e:
        return database_error(str(e), database=database, table=table_name)


async def get_table_comments(database: str, table_name: str) -> str:
    """Retrieve only the comments for a table and its columns.

    Lightweight version of `describe_table_with_comments`.

    Args:
        database (str): REQUIRED. Database name.
        table_name (str): REQUIRED. Table name.

    Returns:
        str: Table and column comments.
    """
    try:
        parts = parse_identifier(table_name)
    except ValueError as exc:
        return validation_error(str(exc), parameter="table_name", value=table_name)
    qualified = format_qualified(parts)

    try:
        async with async_connection(database) as conn:
            table_comment = await conn.fetchval(
                f"SELECT obj_description('{qualified}'::regclass, 'pg_class')"
            )
            table_comment = table_comment if table_comment else "No comment"

            columns = await conn.fetch(
                f"""
                SELECT a.attname, col_description('{qualified}'::regclass, a.attnum)
                FROM pg_attribute a
                WHERE a.attrelid = '{qualified}'::regclass AND a.attnum > 0 AND NOT a.attisdropped
                ORDER BY a.attnum
                """
            )

            output = f"Table '{table_name}' in database '{database}': {table_comment}\nColumns:\n"
            for col in columns:
                col_comment = col["col_description"] or "No comment"
                output += f"  - {col['attname']}: {col_comment}\n"
            return output
    except Exception as e:
        return database_error(str(e), database=database, table=table_name)
