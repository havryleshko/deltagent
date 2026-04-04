from __future__ import annotations

from typing import Any

from googleapiclient.discovery import build

from tools.google_oauth import get_google_credentials
from tools.period_parse import parse_period_to_utc_range

_MAX_EVENTS = 25


def search_calendar_sync(payload: dict[str, Any]) -> str:
    period = str(payload.get("period", ""))
    line_item = str(payload.get("line_item", ""))
    query = str(payload.get("query", ""))
    parsed = parse_period_to_utc_range(period)
    if not parsed:
        return (
            "search_calendar (live): Could not parse period into a month range "
            f"(expected e.g. 'November 2024'): {period!r}"
        )
    time_min, time_max = parsed
    creds = get_google_credentials()
    service = build("calendar", "v3", credentials=creds, cache_discovery=False)
    list_kwargs: dict[str, Any] = {
        "calendarId": "primary",
        "timeMin": time_min,
        "timeMax": time_max,
        "singleEvents": True,
        "orderBy": "startTime",
        "maxResults": _MAX_EVENTS,
    }
    if query and query.strip():
        list_kwargs["q"] = query.strip()[:80]
    events_result = service.events().list(**list_kwargs).execute()
    events = events_result.get("items") or []
    kw = (query + " " + line_item).lower()
    if kw.strip():
        filtered = []
        for ev in events:
            blob = (ev.get("summary", "") + " " + str(ev.get("description", ""))).lower()
            if any(word in blob for word in kw.split() if len(word) > 2):
                filtered.append(ev)
        if filtered:
            events = filtered
    if not events:
        return f"No calendar events in range (live) for period {period!r}."
    lines: list[str] = []
    for ev in events[:15]:
        start = ev.get("start", {}).get("dateTime") or ev.get("start", {}).get("date", "")
        lines.append(f"- {start}: {ev.get('summary', '(no title)')[:200]}")
    return "Calendar (live):\n" + "\n".join(lines)
