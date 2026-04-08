from __future__ import annotations

import json
from typing import Any, Awaitable, Callable

from mcp_client.config import McpServerConfig, load_mcp_connection_state
from mcp_client import client as mcp_client
from tools.base import envelope_to_text

ToolHandler = Callable[[dict[str, Any]], Awaitable[str]]


def _make_mcp_handler(server: McpServerConfig, mcp_tool_name: str) -> ToolHandler:
    async def handler(payload: dict[str, Any]) -> str:
        period = str(payload.get("period", ""))
        date_start = str(payload.get("date_start", ""))
        date_end = str(payload.get("date_end", ""))

        try:
            content = await mcp_client.call_tool(server, mcp_tool_name, payload)
        except Exception as exc:
            return envelope_to_text(
                tool_name=mcp_tool_name,
                period=period,
                date_start=date_start,
                date_end=date_end,
                summary_for_model=f"MCP tool error: {exc}",
                error=str(exc),
            )

        return envelope_to_text(
            tool_name=mcp_tool_name,
            period=period,
            date_start=date_start,
            date_end=date_end,
            summary_for_model=content or f"No content returned by {mcp_tool_name}",
        )

    return handler


def mcp_tool_to_definition(server_name: str, tool: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": tool["name"],
        "description": f"[{server_name}] {tool.get('description', '')}".strip(),
        "input_schema": tool.get("input_schema", {"type": "object", "properties": {}}),
    }


async def build_mcp_tool_registry(
    servers: list[McpServerConfig] | None = None,
) -> tuple[dict[str, ToolHandler], list[dict[str, Any]]]:
    from mcp import client as mcp_client

    if servers is None:
        from mcp_client.config import load_mcp_servers

        servers = load_mcp_servers()

    registry: dict[str, ToolHandler] = {}
    definitions: list[dict[str, Any]] = []

    for server in servers:
        if not server.enabled:
            continue

        try:
            tools = await mcp_client.discover_tools(server)
        except Exception:
            saved = load_mcp_connection_state(server)
            if saved:
                tools = [{"name": t, "description": "", "input_schema": {}} for t in saved.get("tools", [])]
            else:
                continue

        for tool in tools:
            name = tool["name"]
            registry[name] = _make_mcp_handler(server, name)
            definitions.append(mcp_tool_to_definition(server.name, tool))

    return registry, definitions
