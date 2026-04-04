from __future__ import annotations

from typing import Any, Awaitable, Callable

from tools.calendar_tool import search_calendar
from tools.crm_tool import search_crm
from tools.gmail_tool import search_gmail
from tools.slack_tool import search_slack

ToolHandler = Callable[[dict[str, Any]], Awaitable[str]]


def build_mock_tool_registry() -> dict[str, ToolHandler]:
    return {
        "search_slack": search_slack,
        "search_gmail": search_gmail,
        "search_calendar": search_calendar,
        "search_crm": search_crm,
    }


def build_tool_registry() -> dict[str, ToolHandler]:
    """Same handlers as mock registry; each tool branches on DELTAGENT_TOOL_MODE internally."""
    return build_mock_tool_registry()
