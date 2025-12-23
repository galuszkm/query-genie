"""Schema caching mechanism.

Provides thread-safe (in async context) caching for expensive schema
introspection queries.
"""

import time

# Schema cache
# Key: "database:table_name", Value: (timestamp, cached_result)
_SCHEMA_CACHE: dict[str, tuple[float, str]] = {}
SCHEMA_CACHE_TTL = 300  # 5 minutes


def get_cached_schema(database: str, table_name: str) -> str | None:
    """Retrieve schema from cache if valid.

    Args:
        database: Database name.
        table_name: Table name.

    Returns:
        Cached schema string or None if miss/expired.
    """
    key = f"{database}:{table_name}"
    if key in _SCHEMA_CACHE:
        timestamp, data = _SCHEMA_CACHE[key]
        if time.time() - timestamp < SCHEMA_CACHE_TTL:
            return data
        # Expired
        del _SCHEMA_CACHE[key]
    return None


def set_cached_schema(database: str, table_name: str, result: str) -> None:
    """Cache schema result.

    Args:
        database: Database name.
        table_name: Table name.
        result: Schema string to cache.
    """
    key = f"{database}:{table_name}"
    _SCHEMA_CACHE[key] = (time.time(), result)
