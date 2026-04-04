from __future__ import annotations

import os
from typing import Any

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


def search_slack_sync(payload: dict[str, Any]) -> str:
    token = os.environ.get("SLACK_BOT_TOKEN", "").strip()
    if not token:
        return "search_slack (live): Set SLACK_BOT_TOKEN."
    query = " ".join(
        str(payload.get(k, "") or "")
        for k in ("query", "line_item", "period")
    ).strip()
    if not query:
        query = "finance"
    client = WebClient(token=token)
    try:
        resp = client.search_messages(query=query[:200], count=8)
    except SlackApiError as error:
        err = error.response.get("error", str(error))
        return (
            f"Slack search failed (live): {err}. "
            "search.messages often needs a user token with search:read; "
            "use a compatible token or DELTAGENT_TOOL_MODE=mock."
        )
    matches = resp.get("messages", {}).get("matches") or []
    if not matches:
        return f"No Slack messages matched (live). query={query!r}"
    lines: list[str] = []
    for m in matches[:8]:
        text = (m.get("text") or "")[:350]
        ch = m.get("channel", {}).get("name", "?")
        ts = m.get("ts", "")
        user = m.get("username") or m.get("user", "")
        lines.append(f"- #{ch} @{ts} ({user}): {text}")
    return "Slack (live):\n" + "\n".join(lines)
