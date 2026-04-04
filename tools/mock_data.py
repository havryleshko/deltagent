from __future__ import annotations

import json
from pathlib import Path
from typing import Any


FIXTURE_PATH = (
    Path(__file__).resolve().parents[1]
    / "tests"
    / "fixtures"
    / "mock_context_november_2024.json"
)


def _normalize(value: str) -> str:
    return value.strip().lower()


def load_context() -> dict[str, Any]:
    with FIXTURE_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def lookup_context(
    *,
    tool_name: str,
    period: str,
    line_item: str,
    search_scope: str | None = None,
) -> str:
    fixture = load_context()
    canonical_period = fixture.get("period", "")
    if _normalize(period) != _normalize(canonical_period):
        return f"No context found in fixtures for period '{period}'."
    tool_payload = fixture.get("tool_responses", {}).get(tool_name, {})
    line_payload = tool_payload.get(line_item)
    if not line_payload:
        return (
            f"No {tool_name} context found for line item '{line_item}' in {canonical_period}."
        )
    if search_scope and search_scope in line_payload:
        return str(line_payload[search_scope])
    if "broad" in line_payload:
        return str(line_payload["broad"])
    values = [str(value) for value in line_payload.values()]
    return " ".join(values).strip() or (
        f"No {tool_name} context found for line item '{line_item}' in {canonical_period}."
    )
