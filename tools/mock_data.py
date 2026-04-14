from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agent.models import Evidence
from tools.base import envelope_to_text
from tools.period_parse import resolve_period


FIXTURE_PATH = (
    Path(__file__).resolve().parents[1]
    / "tests"
    / "fixtures"
    / "mock_context_november_2024.json"
)

_eval_fixture_path: Path | None = None


def set_eval_fixture_path(path: Path | None) -> None:
    global _eval_fixture_path
    _eval_fixture_path = path


def _effective_fixture_path() -> Path:
    return _eval_fixture_path if _eval_fixture_path is not None else FIXTURE_PATH


def _normalize(value: str) -> str:
    return value.strip().lower()


_LINE_ITEM_ALIASES: dict[str, str] = {
    "marketing programs": "Professional Fees",
    "sales & marketing programs": "Professional Fees",
    "merchant fees": "Professional Fees",
    "freight & packaging": "Office & Facilities",
    "fuel & travel": "Office & Facilities",
    "clinical systems hosting": "Software & Subscriptions",
    "medical compliance & audit": "Professional Fees",
    "repairs & maintenance": "Office & Facilities",
    "contractors": "Salaries",
    "hosting & infrastructure": "Software & Subscriptions",
}


def _resolve_line_item_alias(line_item: str) -> str:
    key = _normalize(line_item)
    return _LINE_ITEM_ALIASES.get(key, line_item)


def load_context(fixture_path: Path | None = None) -> dict[str, Any]:
    path = fixture_path or _effective_fixture_path()
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _mock_timestamp(tool_name: str, line_item: str, search_scope: str | None) -> str:
    tool_order = {
        "search_slack": 12,
        "search_gmail": 18,
        "search_calendar": 22,
        "search_crm": 26,
    }
    day = min(28, max(1, len(line_item)))
    hour = tool_order.get(tool_name, 9)
    minute = 45 if search_scope == "narrow" else 15
    return f"2024-11-{day:02d}T{hour:02d}:{minute:02d}:00Z"


def _build_mock_evidence(
    *,
    tool_name: str,
    line_item: str,
    search_scope: str | None,
    snippet: str,
) -> list[Evidence]:
    suffix = search_scope or "broad"
    source_type = tool_name.removeprefix("search_")
    return [
        Evidence(
            id=f"{source_type}-{line_item.lower().replace(' ', '_')}-{suffix}",
            source_type=source_type,
            timestamp=_mock_timestamp(tool_name, line_item, search_scope),
            snippet=snippet,
            ref=f"{line_item} fixture",
        )
    ]


def lookup_context(
    *,
    tool_name: str,
    period: str,
    line_item: str,
    search_scope: str | None = None,
) -> str:
    fixture = load_context()
    canonical_period = fixture.get("period", "")
    window = resolve_period(period) or resolve_period(canonical_period)
    date_start = window.start_iso if window else ""
    date_end = window.end_iso if window else ""
    if _normalize(period) != _normalize(canonical_period):
        return envelope_to_text(
            tool_name=tool_name,
            period=period,
            date_start=date_start,
            date_end=date_end,
            summary_for_model=f"No context found in fixtures for period '{period}'.",
            error="period_not_found",
        )
    tool_payload = fixture.get("tool_responses", {}).get(tool_name, {})
    lookup_name = _resolve_line_item_alias(line_item)
    line_payload = tool_payload.get(lookup_name)
    if not line_payload:
        return envelope_to_text(
            tool_name=tool_name,
            period=canonical_period,
            date_start=date_start,
            date_end=date_end,
            summary_for_model=(
                f"No {tool_name} context found for line item '{line_item}' in {canonical_period}."
            ),
            error="line_item_not_found",
        )
    if search_scope and search_scope in line_payload:
        summary = str(line_payload[search_scope])
        return envelope_to_text(
            tool_name=tool_name,
            period=canonical_period,
            date_start=date_start,
            date_end=date_end,
            summary_for_model=summary,
            evidence=_build_mock_evidence(
                tool_name=tool_name,
                line_item=line_item,
                search_scope=search_scope,
                snippet=summary,
            ),
        )
    if "broad" in line_payload:
        summary = str(line_payload["broad"])
        return envelope_to_text(
            tool_name=tool_name,
            period=canonical_period,
            date_start=date_start,
            date_end=date_end,
            summary_for_model=summary,
            evidence=_build_mock_evidence(
                tool_name=tool_name,
                line_item=line_item,
                search_scope="broad",
                snippet=summary,
            ),
        )
    values = [str(value) for value in line_payload.values()]
    summary = " ".join(values).strip() or (
        f"No {tool_name} context found for line item '{line_item}' in {canonical_period}."
    )
    return envelope_to_text(
        tool_name=tool_name,
        period=canonical_period,
        date_start=date_start,
        date_end=date_end,
        summary_for_model=summary,
        evidence=_build_mock_evidence(
            tool_name=tool_name,
            line_item=line_item,
            search_scope=search_scope,
            snippet=summary,
        ),
    )
