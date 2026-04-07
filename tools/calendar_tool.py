from __future__ import annotations

import asyncio
from typing import Any

from tools.base import envelope_to_text
from tools.calendar_live import search_calendar_sync
from tools.google_oauth import google_credentials_path
from tools.mock_data import lookup_context
from tools.tool_mode import is_live_tool_mode


async def search_calendar(payload: dict[str, Any]) -> str:
    try:
        period = str(payload.get("period", ""))
        line_item = str(payload.get("line_item", ""))
        search_scope = payload.get("search_scope")
        date_start = str(payload.get("date_start", ""))
        date_end = str(payload.get("date_end", ""))
        if not period or not line_item:
            return envelope_to_text(
                tool_name="search_calendar",
                period=period,
                date_start=date_start,
                date_end=date_end,
                summary_for_model="Tool error (search_calendar): missing required fields period/line_item",
                error="missing_required_fields",
            )
        if not is_live_tool_mode():
            return lookup_context(
                tool_name="search_calendar",
                period=period,
                line_item=line_item,
                search_scope=str(search_scope) if search_scope else None,
            )
        if not google_credentials_path().is_file():
            return envelope_to_text(
                tool_name="search_calendar",
                period=period,
                date_start=date_start,
                date_end=date_end,
                summary_for_model=(
                    "search_calendar (live): OAuth client JSON not found. "
                    "Set GOOGLE_CREDENTIALS_PATH (default credentials.json)."
                ),
                error="missing_google_credentials",
            )
        return await asyncio.to_thread(search_calendar_sync, payload)
    except Exception as error:
        return envelope_to_text(
            tool_name="search_calendar",
            period=str(payload.get("period", "")),
            date_start=str(payload.get("date_start", "")),
            date_end=str(payload.get("date_end", "")),
            summary_for_model=f"Tool error (search_calendar): {error}",
            error="exception",
        )
