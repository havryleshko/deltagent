from __future__ import annotations

from typing import Any

from tools.mock_data import lookup_context


async def search_gmail(payload: dict[str, Any]) -> str:
    try:
        period = str(payload.get("period", ""))
        line_item = str(payload.get("line_item", ""))
        search_scope = payload.get("search_scope")
        if not period or not line_item:
            return "Tool error (search_gmail): missing required fields period/line_item"
        return lookup_context(
            tool_name="search_gmail",
            period=period,
            line_item=line_item,
            search_scope=str(search_scope) if search_scope else None,
        )
    except Exception as error:
        return f"Tool error (search_gmail): {error}"
