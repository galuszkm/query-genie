# PostgreSQL MCP Server

## Overview

A read-only database access layer for AI agents using the Model Context Protocol (MCP). Exposes PostgreSQL databases as discoverable tools for schema exploration, query execution, and data understanding.

**Key characteristics:**
- Read-only by design (blocks INSERT, UPDATE, DELETE, DROP)
- Multi-database support via environment variables
- High-performance async with connection pooling
- Safe for AI exploration without data modification risk

## Key Features

- **Multi-Database Support**: Configure any number of databases via `DATABASE*_URL` variables
- **Fully Asynchronous**: Built on asyncio + asyncpg for non-blocking operations
- **Read-Only Safety**: Query validation blocks all DML/DDL at application layer
- **Performance Optimized**:
  - Lazy connection pooling (2-10 connections per database)
  - Schema caching with 5-minute TTL
  - Parallel cross-database discovery
  - Configurable statement timeouts (max 30s)

## Available Tools

| Tool | Description |
|------|-------------|
| `list_databases` | Discover all configured database sources |
| `list_all_tables` | Search tables across all databases in parallel |
| `list_tables` | List tables in a specific database |
| `describe_table` | Get column types, nullability, and defaults |
| `describe_table_with_comments` | Rich schema with semantic column descriptions |
| `get_query_syntax_help` | Generate correct SQL syntax examples |
| `list_indexes` | Show indexes defined on a table |
| `list_foreign_keys` | Display foreign key relationships |
| `get_table_comments` | Retrieve table and column documentation |
| `query` | Execute validated SELECT queries with limits |
| `get_row_count` | Count rows in a table |
| `sample_data` | Preview actual data from a table |
| `explain_query` | Analyze query execution plans |
| `database_health` | Monitor database size and cache performance |

## Architecture

The module follows a layered architecture:

### Core (`src/core/`)

Foundational services:
- **config.py**: Environment loading, DATABASE*_URL parsing, constants
- **database.py**: asyncpg connection pool management, timeout handling
- **cache.py**: Time-based schema cache (5-min TTL)

### Tools (`src/tools/`)

MCP tool implementations:
- **Discovery**: Find databases and tables (parallel cross-database search)
- **Schema**: Table structure, indexes, foreign keys, comments
- **Query**: SELECT execution, row counts, sampling, EXPLAIN

### Utilities (`src/utils/`)

Cross-cutting concerns:
- **validators.py**: SQL identifier parsing, query safety
- **monitoring.py**: Health checks, connection testing with retries

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE*_URL` | PostgreSQL connection string(s). Format: `postgresql://user:pass@host:port/dbname` | Required |
| `MCP_SERVER_HOST` | Host address to bind | `127.0.0.1` |
| `MCP_SERVER_PORT` | Port number | `8000` |

**Internal constants:**
- Statement timeout: 5s default, 30s max

## Usage

```bash
# Direct execution
python -m src.server

# Docker
docker build -f mcp_postgres/Dockerfile -t mcp-postgres .
docker run -e DATABASE_URL=postgresql://... -p 8000:8000 mcp-postgres
```

AI agents interact by calling tools:
1. `list_databases` → discover available resources
2. `describe_table` → understand schema structure
3. `query` → execute SELECT statements

The server handles all safety validation internally.
