from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from googleapiclient.discovery import build

from agent.models import Evidence
from tools.base import envelope_to_text
from tools.google_oauth import get_google_credentials

_MAX_SNIPPET = 400
_MAX_RESULTS = 8


def search_gmail_sync(payload: dict[str, Any]) -> str:
    period = str(payload.get("period", ""))
    line_item = str(payload.get("line_item", ""))
    query = str(payload.get("query", ""))
    scope = payload.get("search_scope")
    date_start = str(payload.get("date_start", ""))
    date_end = str(payload.get("date_end", ""))
    creds = get_google_credentials()
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    parts = [query, line_item, period]
    if date_start:
        after_dt = datetime.fromisoformat(date_start.replace("Z", "+00:00"))
        parts.append(f"after:{after_dt.strftime('%Y/%m/%d')}")
    if date_end:
        before_dt = datetime.fromisoformat(date_end.replace("Z", "+00:00")) + timedelta(days=1)
        parts.append(f"before:{before_dt.strftime('%Y/%m/%d')}")
    if scope == "narrow":
        q = " ".join(p for p in parts if p).strip()
        if len(q) > 180:
            q = q[:180]
    else:
        q = " ".join(p for p in parts if p).strip()[:220]
    if not q:
        q = line_item or period or "finance"
    result = (
        service.users()
        .messages()
        .list(userId="me", q=q, maxResults=_MAX_RESULTS)
        .execute()
    )
    messages = result.get("messages") or []
    if not messages:
        return envelope_to_text(
            tool_name="search_gmail",
            period=period,
            date_start=date_start,
            date_end=date_end,
            summary_for_model=f"No Gmail messages matched query (live). q={q!r}",
            error="no_matches",
        )
    evidence: list[Evidence] = []
    summary_lines: list[str] = []
    for item in messages:
        mid = item["id"]
        msg = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=mid,
                format="metadata",
                metadataHeaders=["Subject", "From", "Date"],
            )
            .execute()
        )
        headers = {
            h["name"]: h["value"]
            for h in msg.get("payload", {}).get("headers", [])
            if h.get("name") and h.get("value")
        }
        subj = headers.get("Subject", "(no subject)")[:200]
        sender = headers.get("From", "")[:120]
        date = headers.get("Date", "")
        snippet = (msg.get("snippet") or "")[:_MAX_SNIPPET]
        summary_lines.append(f"{date} | {sender} | {subj} | {snippet}")
        evidence.append(
            Evidence(
                id=f"gmail-{mid}",
                source_type="gmail",
                timestamp=date,
                snippet=snippet,
                ref=subj,
            )
        )
    return envelope_to_text(
        tool_name="search_gmail",
        period=period,
        date_start=date_start,
        date_end=date_end,
        summary_for_model="; ".join(summary_lines),
        evidence=evidence,
    )
