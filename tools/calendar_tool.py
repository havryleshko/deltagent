from __future__ import annotations

import asyncio
from typing import Any

from tools.calendar_live import search_calendar_sync
from tools.google_oauth import google_credentials_path
from tools.mock_data import lookup_context
from tools.tool_mode import is_live_tool_mode


async def search_calendar(payload: dict[str, Any]) -> str:
    try:
        period = str(payload.get("period", ""))
        line_item = str(payload.get("line_item", ""))
        search_scope = payload.get("search_scope")
        if not period or not line_item:
            return "Tool error (search_calendar): missing required fields period/line_item"
        if not is_live_tool_mode():
            return lookup_context(
                tool_name="search_calendar",
                period=period,
                line_item=line_item,
                search_scope=str(search_scope) if search_scope else None,
            )
        if not google_credentials_path().is_file():
            return (
                "search_calendar (live): OAuth client JSON not found. "
                "Set GOOGLE_CREDENTIALS_PATH (default credentials.json)."
            )
        return await asyncio.to_thread(search_calendar_sync, payload)
    except Exception as error:
        return f"Tool error (search_calendar): {error}"
