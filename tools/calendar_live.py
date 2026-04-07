from __future__ import annotations

from typing import Any

from googleapiclient.discovery import build

from agent.models import Evidence
from tools.base import envelope_to_text
from tools.google_oauth import get_google_credentials
from tools.period_parse import parse_period_to_utc_range

_MAX_EVENTS = 25


def search_calendar_sync(payload: dict[str, Any]) -> str:
    period = str(payload.get("period", ""))
    line_item = str(payload.get("line_item", ""))
    query = str(payload.get("query", ""))
    date_start = str(payload.get("date_start", ""))
    date_end = str(payload.get("date_end", ""))
    parsed = (date_start, date_end) if date_start and date_end else parse_period_to_utc_range(period)
    if not parsed:
        return envelope_to_text(
            tool_name="search_calendar",
            period=period,
            date_start=date_start,
            date_end=date_end,
            summary_for_model=(
                "search_calendar (live): Could not parse period into a month range "
                f"(expected e.g. 'November 2024'): {period!r}"
            ),
            error="unparsed_period",
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
        return envelope_to_text(
            tool_name="search_calendar",
            period=period,
            date_start=time_min,
            date_end=time_max,
            summary_for_model=f"No calendar events in range (live) for period {period!r}.",
            error="no_matches",
        )
    evidence: list[Evidence] = []
    summary_lines: list[str] = []
    for ev in events[:15]:
        start = ev.get("start", {}).get("dateTime") or ev.get("start", {}).get("date", "")
        title = ev.get("summary", "(no title)")[:200]
        summary_lines.append(f"{start}: {title}")
        evidence.append(
            Evidence(
                id=f"calendar-{ev.get('id', title)}",
                source_type="calendar",
                timestamp=start,
                snippet=str(ev.get("description", "") or title),
                ref=title,
            )
        )
    return envelope_to_text(
        tool_name="search_calendar",
        period=period,
        date_start=time_min,
        date_end=time_max,
        summary_for_model="; ".join(summary_lines),
        evidence=evidence,
    )
