from __future__ import annotations

import asyncio
from typing import Any

import httpx

from mcp_client.config import McpServerConfig


async def _sse_discover_tools(url: str) -> list[dict[str, Any]]:
    from mcp import ClientSession
    from mcp.client.sse import sse_client

    async with sse_client(url) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            return [
                {
                    "name": t.name,
                    "description": t.description or "",
                    "input_schema": t.inputSchema if hasattr(t, "inputSchema") else {},
                }
                for t in (result.tools or [])
            ]


async def _sse_call_tool(url: str, tool_name: str, arguments: dict[str, Any]) -> str:
    from mcp import ClientSession
    from mcp.client.sse import sse_client

    async with sse_client(url) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            parts = []
            for block in result.content or []:
                if hasattr(block, "text") and block.text:
                    parts.append(str(block.text))
            return "\n".join(parts) if parts else ""


async def discover_tools(
    server: McpServerConfig,
    timeout: float = 10.0,
) -> list[dict[str, Any]]:
    """Connect to the MCP server and return its tool definitions."""
    try:
        return await asyncio.wait_for(_sse_discover_tools(server.url), timeout=timeout)
    except asyncio.TimeoutError:
        raise ConnectionError(f"Timeout connecting to {server.name} ({server.url})")
    except Exception as exc:
        raise ConnectionError(f"Could not connect to {server.name}: {exc}") from exc


async def call_tool(
    server: McpServerConfig,
    tool_name: str,
    arguments: dict[str, Any],
    timeout: float = 30.0,
) -> str:
    """Call a tool on the MCP server and return the text response."""
    try:
        return await asyncio.wait_for(
            _sse_call_tool(server.url, tool_name, arguments), timeout=timeout
        )
    except asyncio.TimeoutError:
        raise ConnectionError(f"Tool call timed out on {server.name}/{tool_name}")
    except Exception as exc:
        raise ConnectionError(f"MCP tool call failed ({server.name}/{tool_name}): {exc}") from exc


async def ping(server: McpServerConfig, timeout: float = 5.0) -> bool:
    """Return True if the server URL is reachable over HTTP."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(server.url)
            return resp.status_code < 500
    except Exception:
        return False
