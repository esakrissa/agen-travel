# Supabase MCP

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

A Supabase MCP server for LangGraph integrations with index tuning, explain plans, health checks, and SQL execution.

## Overview

**Supabase MCP** is a Model Context Protocol (MCP) server that connects your AI agents to Supabase databases, enabling them to interact with and analyze your data effectively.

Features include:

- **🔍 Database Health** - Analyze index health, connection utilization, buffer cache, vacuum health, and more
- **⚡ Index Tuning** - Find the best indexing solution for your workload
- **📈 Query Plans** - Review EXPLAIN plans and simulate hypothetical indexes
- **🧠 Schema Intelligence** - Context-aware SQL generation based on database schema
- **🛡️ Safe SQL Execution** - Configurable access control with read-only mode

## Quick Start

### Prerequisites

Before getting started, ensure you have:
1. Access credentials for your Supabase database
2. Python 3.12 or higher

### Installation

Install dependencies with `uv` using `pyproject.toml`:

```bash
cd mcp/supabase
uv sync
```

Alternative installation methods:

```bash
# Install only production dependencies
uv pip install -e .

# Install with development dependencies
uv pip install -e .[dev]

# Install in a new virtual environment
uv venv
uv pip install -e .
```

### Usage

Configure the MCP server in your LangGraph or Claude configuration:

```json
{
  "supabase": {
    "command": "uv",
    "args": [
      "--directory",
      "mcp/supabase",
      "run",
      "src/supabase_mcp/main.py"
    ],
    "env": {
      "DATABASE_URI": "postgresql://username:password@localhost:5432/dbname",
      "PATH": "/path/to/your/env/bin:/usr/local/bin:/usr/bin:/bin"
    },
    "transport": "stdio"
  }
}
```

## MCP Server API

Supabase MCP provides functionality via [MCP tools](https://modelcontextprotocol.io/docs/concepts/tools).

Available tools:

| Tool Name | Description |
|-----------|-------------|
| `list_schemas` | Lists all database schemas available |
| `list_objects` | Lists database objects (tables, views, sequences, extensions) |
| `get_object_details` | Provides information about specific database objects |
| `execute_sql` | Executes SQL statements on the database |
| `explain_query` | Gets the execution plan for a SQL query |
| `get_top_queries` | Reports the slowest SQL queries |
| `analyze_workload_indexes` | Analyzes the database workload and recommends indexes |
| `analyze_query_indexes` | Analyzes specific SQL queries and recommends indexes |
| `analyze_db_health` | Performs comprehensive health checks |

## Postgres Extension Installation (Optional)

For full functionality, ensure your Supabase database has the following extensions enabled:

```sql
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS hypopg;
```

## License

MIT