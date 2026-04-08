from __future__ import annotations

from typing import Any, Awaitable, Callable

from tools.calendar_tool import search_calendar
from tools.crm_tool import search_crm
from tools.gmail_tool import search_gmail
from tools.period_parse import PeriodWindow
from tools.slack_tool import search_slack

ToolHandler = Callable[[dict[str, Any]], Awaitable[str]]


def build_mock_tool_registry() -> dict[str, ToolHandler]:
    return {
        "search_slack": search_slack,
        "search_gmail": search_gmail,
        "search_calendar": search_calendar,
        "search_crm": search_crm,
    }


def _with_period_bounds(
    handler: ToolHandler, period_window: PeriodWindow | None
) -> ToolHandler:
    if period_window is None:
        return handler

    async def wrapped(payload: dict[str, Any]) -> str:
        next_payload = dict(payload)
        next_payload["period"] = period_window.label
        next_payload["date_start"] = period_window.start_iso
        next_payload["date_end"] = period_window.end_iso
        return await handler(next_payload)

    return wrapped


def build_tool_registry(period_window: PeriodWindow | None = None) -> dict[str, ToolHandler]:
    return {
        name: _with_period_bounds(handler, period_window)
        for name, handler in build_mock_tool_registry().items()
    }


async def build_tool_registry_with_mcp(
    period_window: PeriodWindow | None = None,
) -> tuple[dict[str, ToolHandler], list[dict[str, Any]]]:
    from mcp_client.config import load_mcp_servers
    from mcp_client.registry import build_mcp_tool_registry
    from tools.definitions import TOOL_DEFINITIONS

    local = build_tool_registry(period_window)
    servers = load_mcp_servers()
    if not servers:
        return local, []

    mcp_registry, mcp_definitions = await build_mcp_tool_registry(servers)
    merged = {**mcp_registry, **local}
    new_defs = [d for d in mcp_definitions if d["name"] not in {t["name"] for t in TOOL_DEFINITIONS}]
    return merged, new_defs
