"""
Nautilus PostgreSQL MCP Connector
Connects the Nautilus platform to PostgreSQL databases via Model Context Protocol.

Based on the MCP SDK pattern from ahmedmustahid/postgres-mcp-server
"""
import os
import json
from typing import Any, Optional
from dataclasses import dataclass, field

# MCP SDK imports - requires: pip install mcp
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent, Resource
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False


@dataclass
class PostgresConfig:
    """Configuration for PostgreSQL connection."""
    host: str = os.getenv("POSTGRES_HOST", "localhost")
    port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    database: str = os.getenv("POSTGRES_DB", "nautilus")
    user: str = os.getenv("POSTGRES_USER", "nautilus")
    password: str = os.getenv("POSTGRES_PASSWORD", "")
    ssl_mode: str = os.getenv("POSTGRES_SSL_MODE", "prefer")


@dataclass 
class NautilusPostgresConnector:
    """MCP Connector for PostgreSQL databases in Nautilus ecosystem."""
    config: PostgresConfig = field(default_factory=PostgresConfig)
    server_name: str = "nautilus-postgres-connector"
    version: str = "0.1.0"
    
    def __post_init__(self):
        self._tools = []
        self._resources = []
        self._connection = None
    
    def get_connection(self):
        """Get or create database connection."""
        if not MCP_AVAILABLE:
            return None
            
        if self._connection is None:
            try:
                import psycopg2
                self._connection = psycopg2.connect(
                    host=self.config.host,
                    port=self.config.port,
                    database=self.config.database,
                    user=self.config.user,
                    password=self.config.password,
                    sslmode=self.config.ssl_mode
                )
            except ImportError:
                # psycopg2 not available, return mock for development
                return MockConnection()
            except Exception as e:
                print(f"PostgreSQL connection failed: {e}")
                return None
        return self._connection

    def execute_query(self, query: str, params: Optional[tuple] = None) -> dict:
        """Execute a read-only query and return results."""
        conn = self.get_connection()
        if conn is None:
            return {"status": "error", "message": "Connection unavailable"}
            
        try:
            with conn.cursor() as cur:
                cur.execute(query, params or ())
                if cur.description:
                    columns = [desc[0] for desc in cur.description]
                    rows = cur.fetchall()
                    return {
                        "status": "success",
                        "columns": columns,
                        "rows": [dict(zip(columns, row)) for row in rows],
                        "row_count": len(rows)
                    }
                return {"status": "success", "row_count": 0}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def list_tables(self) -> dict:
        """List all tables in the public schema."""
        return self.execute_query("""
            SELECT table_name, table_type 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)

    def describe_table(self, table_name: str) -> dict:
        """Get schema for a specific table."""
        return self.execute_query("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = %s AND table_schema = 'public'
            ORDER BY ordinal_position
        """, (table_name,))


class MockConnection:
    """Mock connection for development/testing without PostgreSQL."""
    def cursor(self):
        return MockCursor()
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass


class MockCursor:
    """Mock cursor that returns sample data."""
    description = [("table_name",), ("table_type",)]
    
    def execute(self, query, params=None):
        pass
    
    def fetchall(self):
        return [("agents", "BASE TABLE"), ("tasks", "BASE TABLE"), ("memories", "BASE TABLE")]


# MCP Server handlers
async def handle_list_tools():
    """Return available tools."""
    return [
        Tool(
            name="pg_list_tables",
            description="List all tables in the PostgreSQL database",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="pg_describe_table",
            description="Get schema information for a specific table",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the table to describe"
                    }
                },
                "required": ["table_name"]
            }
        ),
        Tool(
            name="pg_query",
            description="Execute a read-only SQL query",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL query to execute (SELECT only)"
                    }
                },
                "required": ["query"]
            }
        )
    ]


async def handle_call_tool(name: str, arguments: dict, connector: NautilusPostgresConnector) -> list[TextContent]:
    """Handle tool calls from MCP clients."""
    result = {"error": f"Unknown tool: {name}"}
    
    if name == "pg_list_tables":
        result = connector.list_tables()
    elif name == "pg_describe_table":
        table_name = arguments.get("table_name", "")
        result = connector.describe_table(table_name)
    elif name == "pg_query":
        query = arguments.get("query", "")
        if not query.strip().upper().startswith("SELECT"):
            result = {"error": "Only SELECT queries are allowed"}
        else:
            result = connector.execute_query(query)
    
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def handle_list_resources():
    """Return available resources."""
    return [
        Resource(
            uri="postgres://schema/tables",
            name="Database Schema Overview",
            description="Overview of all tables in the database",
            mimeType="application/json"
        )
    ]


async def run_server():
    """Run the MCP server."""
    if not MCP_AVAILABLE:
        print("MCP SDK not available. Install with: pip install mcp")
        print("Running in demo mode with mock data.")
        connector = NautilusPostgresConnector()
        print(f"Connector ready: {connector.server_name} v{connector.version}")
        print(f"Tables: {connector.list_tables()}")
        return
    
    server = Server(nautilus_mcp_postgres.server_name)
    connector = NautilusPostgresConnector()
    
    @server.list_tools()
    async def list_tools():
        return await handle_list_tools()
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        return await handle_call_tool(name, arguments, connector)
    
    @server.list_resources()
    async def list_resources():
        return await handle_list_resources()
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_server())
