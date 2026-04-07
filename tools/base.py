from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from agent.models import Evidence


@dataclass
class ToolResultEnvelope:
    tool_name: str
    period: str
    date_start: str
    date_end: str
    summary_for_model: str
    evidence: list[Evidence] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_text(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=True)


def envelope_to_text(
    *,
    tool_name: str,
    period: str,
    date_start: str,
    date_end: str,
    summary_for_model: str,
    evidence: list[Evidence] | None = None,
    error: str | None = None,
) -> str:
    return ToolResultEnvelope(
        tool_name=tool_name,
        period=period,
        date_start=date_start,
        date_end=date_end,
        summary_for_model=summary_for_model,
        evidence=evidence or [],
        error=error,
    ).to_text()
