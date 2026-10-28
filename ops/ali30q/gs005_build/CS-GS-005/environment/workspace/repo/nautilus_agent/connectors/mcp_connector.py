"""
MCP (Model Context Protocol) Connector for Nautilus Agent Platform.

Enables Nautilus agents to discover, connect to, and execute tasks via
any MCP-compatible server. This fills the protocol-interoperability gap
identified in the 2025 A2A/MCP ecosystem research.

Based on: https://modelcontextprotocol.io/
Status: EXPERIMENTAL — do not use in production without testing.
"""

import json
import asyncio
import httpx
from typing import Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class MCPError(Exception):
    """Base exception for MCP operations."""
    pass


class ConnectionError(MCPError):
    """Raised when MCP server connection fails."""
    pass


class ToolNotFoundError(MCPError):
    """Raised when requested tool doesn't exist on MCP server."""
    pass


@dataclass
class MCPTool:
    """Represents a callable tool exposed by an MCP server."""
    name: str
    description: str
    input_schema: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "MCPTool":
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            input_schema=data.get("inputSchema", {}),
        )


@dataclass
class MCPResource:
    """Represents a resource available from an MCP server."""
    uri: str
    name: str
    mime_type: str = "application/octet-stream"
    description: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "MCPResource":
        return cls(
            uri=data.get("uri", ""),
            name=data.get("name", ""),
            mime_type=data.get("mimeType", "application/octet-stream"),
            description=data.get("description", ""),
        )


class MCPClient:
    """
    Client for connecting Nautilus agents to MCP servers.

    Usage:
        client = MCPClient("https://mcp-server.example.com")
        await client.connect()
        tools = await client.list_tools()
        result = await client.call_tool("my_tool", {"arg": "value"})
        await client.disconnect()
    """

    def __init__(self, server_url: str, timeout: float = 30.0):
        self.server_url = server_url.rstrip("/")
        self.timeout = timeout
        self._session_id: Optional[str] = None
        self._tools: list[MCPTool] = []
        self._resources: list[MCPResource] = []
        self._connected = False
        self._client: Optional[httpx.AsyncClient] = None

    async def connect(self) -> dict[str, Any]:
        """
        Establish connection to MCP server and fetch capabilities.
        Returns server info dict with name, version, capabilities.
        Raises ConnectionError on failure.
        """
        if self._connected:
            return {"status": "already_connected"}

        try:
            self._client = httpx.AsyncClient(timeout=self.timeout)
            response = await self._client.post(
                f"{self.server_url}/mcp/initialize",
                json={"protocolVersion": "2024-11-05", "capabilities": {}},
            )
            response.raise_for_status()
            data = response.json()
            self._session_id = data.get("sessionId", "")
            self._connected = True

            # Fetch available tools
            await self._refresh_tools()
            # Fetch available resources
            await self._refresh_resources()

            return data

        except httpx.HTTPStatusError as e:
            raise ConnectionError(f"MCP server returned {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise ConnectionError(f"Failed to connect to MCP server: {e}") from e

    async def _refresh_tools(self) -> None:
        """Internal: fetch and cache tool list from server."""
        if not self._connected or not self._client:
            return
        response = await self._client.post(
            f"{self.server_url}/mcp/tools/list",
            json={"sessionId": self._session_id} if self._session_id else {},
        )
        response.raise_for_status()
        tools_data = response.json().get("tools", [])
        self._tools = [MCPTool.from_dict(t) for t in tools_data]

    async def _refresh_resources(self) -> None:
        """Internal: fetch and cache resource list from server."""
        if not self._connected or not self._client:
            return
        response = await self._client.post(
            f"{self.server_url}/mcp/resources/list",
            json={"sessionId": self._session_id} if self._session_id else {},
        )
        response.raise_for_status()
        resources_data = response.json().get("resources", [])
        self._resources = [MCPResource.from_dict(r) for r in resources_data]

    async def list_tools(self) -> list[MCPTool]:
        """Return cached list of available tools."""
        if not self._connected:
            raise MCPError("Not connected. Call connect() first.")
        return self._tools

    async def list_resources(self) -> list[MCPResource]:
        """Return cached list of available resources."""
        if not self._connected:
            raise MCPError("Not connected. Call connect() first.")
        return self._resources

    async def call_tool(
        self, tool_name: str, arguments: Optional[dict[str, Any]] = None
    ) -> Any:
        """
        Call a tool on the MCP server.
        Returns the tool's output (structure depends on server).
        Raises ToolNotFoundError if tool doesn't exist.
        """
        if not self._connected or not self._client:
            raise MCPError("Not connected. Call connect() first.")

        # Check tool exists locally
        tool_names = [t.name for t in self._tools]
        if tool_name not in tool_names:
            raise ToolNotFoundError(f"Tool '{tool_name}' not found. Available: {tool_names}")

        payload: dict[str, Any] = {"name": tool_name}
        if arguments:
            payload["arguments"] = arguments
        if self._session_id:
            payload["sessionId"] = self._session_id

        response = await self._client.post(
            f"{self.server_url}/mcp/tools/call", json=payload
        )
        response.raise_for_status()
        return response.json()

    async def read_resource(self, uri: str) -> dict[str, Any]:
        """Read a specific resource by URI from the MCP server."""
        if not self._connected or not self._client:
            raise MCPError("Not connected. Call connect() first.")

        payload: dict[str, Any] = {"uri": uri}
        if self._session_id:
            payload["sessionId"] = self._session_id

        response = await self._client.post(
            f"{self.server_url}/mcp/resources/read", json=payload
        )
        response.raise_for_status()
        return response.json()

    async def disconnect(self) -> None:
        """Close the connection to the MCP server."""
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False
        self._session_id = None
        self._tools = []
        self._resources = []

    @property
    def is_connected(self) -> bool:
        return self._connected


# ---------------------------------------------------------------------------
# Nautilus-specific integration layer
# ---------------------------------------------------------------------------

class MCPToolResult:
    """Standardized result format for MCP tool calls in Nautilus."""
    def __init__(self, tool_name: str, success: bool, output: Any = None, error: str = None):
        self.tool_name = tool_name
        self.success = success
        self.output = output
        self.error = error
        self.metadata = {"mcp_server": "unknown"}

    def to_nautilus_task_result(self) -> dict[str, Any]:
        return {
            "tool": self.tool_name,
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata,
        }


async def execute_mcp_task(
    server_url: str, tool_name: str, arguments: Optional[dict[str, Any]] = None
) -> MCPToolResult:
    """
    Execute a single MCP tool task from a Nautilus agent.
    Convenience wrapper around MCPClient for platform integration.
    """
    client = MCPClient(server_url)
    try:
        await client.connect()
        result = await client.call_tool(tool_name, arguments)
        return MCPToolResult(tool_name, success=True, output=result)
    except MCPError as e:
        return MCPToolResult(tool_name, success=False, error=str(e))
    finally:
        await client.disconnect()


# ---------------------------------------------------------------------------
# MCP Server Registry (for discovery within Nautilus platform)
# ---------------------------------------------------------------------------

@dataclass
class MCPServerEntry:
    url: str
    name: str
    description: str = ""
    tags: list[str] = field(default_factory=list)
    health_status: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "name": self.name,
            "description": self.description,
            "tags": self.tags,
            "health_status": self.health_status,
        }


class MCPServerRegistry:
    """
    Registry of known MCP servers for the Nautilus platform.
    Agents can query this to discover available MCP tools.
    """

    def __init__(self):
        self._servers: dict[str, MCPServerEntry] = {}

    def register(self, entry: MCPServerEntry) -> None:
        self._servers[entry.url] = entry

    def unregister(self, url: str) -> bool:
        return self._servers.pop(url, None) is not None

    def get(self, url: str) -> Optional[MCPServerEntry]:
        return self._servers.get(url)

    def list_all(self) -> list[MCPServerEntry]:
        return list(self._servers.values())

    def find_by_tag(self, tag: str) -> list[MCPServerEntry]:
        return [s for s in self._servers.values() if tag in s.tags]

    def find_by_name(self, name: str) -> list[MCPServerEntry]:
        q = name.lower()
        return [s for s in self._servers.values() if q in s.name.lower()]


# ---------------------------------------------------------------------------
# Example usage (can be run standalone for testing)
# ---------------------------------------------------------------------------

async def demo():
    """Example: connect to a public MCP server and list tools."""
    import os

    server_url = os.environ.get("MCP_SERVER_URL", "https://api.example.com")
    client = MCPClient(server_url)

    try:
        info = await client.connect()
        print(f"Connected to MCP server: {info}")

        tools = await client.list_tools()
        print(f"Available tools ({len(tools)}):")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")

        resources = await client.list_resources()
        print(f"Available resources ({len(resources)}):")
        for res in resources:
            print(f"  - {res.name} ({res.uri})")

    except ConnectionError as e:
        print(f"Connection failed: {e}")
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(demo())
