from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from agent.models import Evidence
from tools.base import envelope_to_text


def search_slack_sync(payload: dict[str, Any]) -> str:
    token = os.environ.get("SLACK_BOT_TOKEN", "").strip()
    period = str(payload.get("period", ""))
    date_start = str(payload.get("date_start", ""))
    date_end = str(payload.get("date_end", ""))
    if not token:
        return envelope_to_text(
            tool_name="search_slack",
            period=period,
            date_start=date_start,
            date_end=date_end,
            summary_for_model="search_slack (live): Set SLACK_BOT_TOKEN.",
            error="missing_slack_token",
        )
    query = " ".join(
        str(payload.get(k, "") or "")
        for k in ("query", "line_item", "period")
    ).strip()
    if date_start:
        after_dt = datetime.fromisoformat(date_start.replace("Z", "+00:00"))
        query = f"{query} after:{after_dt.strftime('%Y-%m-%d')}".strip()
    if date_end:
        before_dt = datetime.fromisoformat(date_end.replace("Z", "+00:00")) + timedelta(days=1)
        query = f"{query} before:{before_dt.strftime('%Y-%m-%d')}".strip()
    if not query:
        query = "finance"
    client = WebClient(token=token)
    try:
        resp = client.search_messages(query=query[:200], count=8)
    except SlackApiError as error:
        err = error.response.get("error", str(error))
        return envelope_to_text(
            tool_name="search_slack",
            period=period,
            date_start=date_start,
            date_end=date_end,
            summary_for_model=(
                f"Slack search failed (live): {err}. "
                "search.messages often needs a user token with search:read; "
                "use a compatible token or DELTAGENT_TOOL_MODE=mock."
            ),
            error="slack_api_error",
        )
    matches = resp.get("messages", {}).get("matches") or []
    if not matches:
        return envelope_to_text(
            tool_name="search_slack",
            period=str(payload.get("period", "")),
            date_start=date_start,
            date_end=date_end,
            summary_for_model=f"No Slack messages matched (live). query={query!r}",
            error="no_matches",
        )
    evidence: list[Evidence] = []
    summary_lines: list[str] = []
    for m in matches[:8]:
        text = (m.get("text") or "")[:350]
        ch = m.get("channel", {}).get("name", "?")
        ts = m.get("ts", "")
        user = m.get("username") or m.get("user", "")
        summary_lines.append(f"#{ch} @{ts} ({user}): {text}")
        evidence.append(
            Evidence(
                id=f"slack-{m.get('iid', ts)}",
                source_type="slack",
                timestamp=ts,
                snippet=text,
                ref=f"#{ch}",
            )
        )
    return envelope_to_text(
        tool_name="search_slack",
        period=period,
        date_start=date_start,
        date_end=date_end,
        summary_for_model="; ".join(summary_lines),
        evidence=evidence,
    )
