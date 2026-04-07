from __future__ import annotations

import asyncio
from typing import Any

from tools.base import envelope_to_text
from tools.mock_data import lookup_context
from tools.slack_live import search_slack_sync
from tools.tool_mode import is_live_tool_mode


async def search_slack(payload: dict[str, Any]) -> str:
    try:
        period = str(payload.get("period", ""))
        line_item = str(payload.get("line_item", ""))
        search_scope = payload.get("search_scope")
        date_start = str(payload.get("date_start", ""))
        date_end = str(payload.get("date_end", ""))
        if not period or not line_item:
            return envelope_to_text(
                tool_name="search_slack",
                period=period,
                date_start=date_start,
                date_end=date_end,
                summary_for_model="Tool error (search_slack): missing required fields period/line_item",
                error="missing_required_fields",
            )
        if not is_live_tool_mode():
            return lookup_context(
                tool_name="search_slack",
                period=period,
                line_item=line_item,
                search_scope=str(search_scope) if search_scope else None,
            )
        return await asyncio.to_thread(search_slack_sync, payload)
    except Exception as error:
        return envelope_to_text(
            tool_name="search_slack",
            period=str(payload.get("period", "")),
            date_start=str(payload.get("date_start", "")),
            date_end=str(payload.get("date_end", "")),
            summary_for_model=f"Tool error (search_slack): {error}",
            error="exception",
        )
