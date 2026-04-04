from __future__ import annotations

from typing import Any

from googleapiclient.discovery import build

from tools.google_oauth import get_google_credentials

_MAX_SNIPPET = 400
_MAX_RESULTS = 8


def search_gmail_sync(payload: dict[str, Any]) -> str:
    period = str(payload.get("period", ""))
    line_item = str(payload.get("line_item", ""))
    query = str(payload.get("query", ""))
    scope = payload.get("search_scope")
    creds = get_google_credentials()
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    parts = [query, line_item, period]
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
        return f"No Gmail messages matched query (live). q={q!r}"
    lines: list[str] = []
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
        lines.append(f"- {date} | {sender}\n  Subject: {subj}\n  {snippet}")
    return "Gmail (live):\n" + "\n\n".join(lines)
