"""PostgreSQL MCP Server with read-only tools for AI agents."""

import asyncio
import logging

from mcp.server.fastmcp import FastMCP

from .core.config import DATABASE_URLS, settings
from .core.database import close_pools
from .core.logging_config import configure_mcp_logging
from .tools import discovery, query, schema
from .utils import monitoring
from .utils.monitoring import test_all_connections

# Configure logging to stderr (MCP protocol requirement)
configure_mcp_logging(level="INFO")
logger = logging.getLogger(__name__)

if not DATABASE_URLS:
    raise RuntimeError(
        "No DATABASE*_URL environment variables found. Please configure at least one database."
    )


def create_mcp_server() -> FastMCP:
    """Create and configure the MCP server with all tools."""
    mcp = FastMCP(
        "PostgreSQL MCP Server",
        stateless_http=True,
        json_response=True,
        host=settings.mcp_server_host,
        port=settings.mcp_server_port,
    )

    # Register tools (schemas auto-generated from type hints and docstrings)
    # Discovery
    mcp.tool()(discovery.list_databases)
    mcp.tool()(discovery.list_all_tables)
    mcp.tool()(discovery.list_tables)

    # Schema
    mcp.tool()(schema.describe_table)
    mcp.tool()(schema.describe_table_with_comments)
    mcp.tool()(schema.get_query_syntax_help)
    mcp.tool()(schema.list_indexes)
    mcp.tool()(schema.list_foreign_keys)
    mcp.tool()(schema.get_table_comments)

    # Query
    mcp.tool()(query.query)
    mcp.tool()(query.get_row_count)
    mcp.tool()(query.sample_data)
    mcp.tool()(query.explain_query)

    # Monitoring
    mcp.tool()(monitoring.database_health)
    mcp.tool()(monitoring.mcp_server_health)

    return mcp


mcp = create_mcp_server()

if __name__ == "__main__":
    # Run async test before starting server
    if not asyncio.run(test_all_connections()):
        exit(1)

    # Close the test pools gracefully - they're attached to a closed event loop
    # Pools will be lazily created on first use in the server's event loop
    asyncio.run(close_pools())
    logger.info("Connection test passed. Pools will be initialized on first use.")

    mcp.run(transport="streamable-http")
