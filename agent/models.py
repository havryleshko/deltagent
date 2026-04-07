from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


ReviewStatus = Literal["pending", "accepted", "edited", "flagged"]


@dataclass
class Evidence:
    id: str
    source_type: str
    timestamp: str
    snippet: str
    ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Evidence":
        return cls(
            id=str(payload.get("id", "")),
            source_type=str(payload.get("source_type", "")),
            timestamp=str(payload.get("timestamp", "")),
            snippet=str(payload.get("snippet", "")),
            ref=str(payload.get("ref", "")),
        )


@dataclass
class ParsedLineItem:
    header: str
    commentary: str
    sources: list[Evidence] = field(default_factory=list)
    review_status: ReviewStatus = "pending"
    edited_commentary: str | None = None
    flagged_reason: str | None = None

    @property
    def final_commentary(self) -> str:
        if self.review_status == "edited" and self.edited_commentary:
            return self.edited_commentary
        return self.commentary

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["sources"] = [source.to_dict() for source in self.sources]
        return data

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ParsedLineItem":
        return cls(
            header=str(payload.get("header", "")),
            commentary=str(payload.get("commentary", "")),
            sources=[
                Evidence.from_dict(item) for item in payload.get("sources", []) or []
            ],
            review_status=payload.get("review_status", "pending"),
            edited_commentary=payload.get("edited_commentary"),
            flagged_reason=payload.get("flagged_reason"),
        )


@dataclass
class ToolTrace:
    tool_name: str
    tool_use_id: str
    input_payload: dict[str, Any]
    output_text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ToolTrace":
        return cls(
            tool_name=str(payload.get("tool_name", "")),
            tool_use_id=str(payload.get("tool_use_id", "")),
            input_payload=dict(payload.get("input_payload", {}) or {}),
            output_text=str(payload.get("output_text", "")),
        )


@dataclass
class AgentRun:
    run_id: str
    period_label: str
    period_start: str
    period_end: str
    currency_symbol: str
    raw_text: str
    executive_summary: str = ""
    line_items: list[ParsedLineItem] = field(default_factory=list)
    insignificant: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    tool_diagnostics: list[str] = field(default_factory=list)
    tool_traces: list[ToolTrace] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "period_label": self.period_label,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "currency_symbol": self.currency_symbol,
            "raw_text": self.raw_text,
            "executive_summary": self.executive_summary,
            "line_items": [item.to_dict() for item in self.line_items],
            "insignificant": list(self.insignificant),
            "gaps": list(self.gaps),
            "tool_diagnostics": list(self.tool_diagnostics),
            "tool_traces": [trace.to_dict() for trace in self.tool_traces],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AgentRun":
        return cls(
            run_id=str(payload.get("run_id", "")),
            period_label=str(payload.get("period_label", "")),
            period_start=str(payload.get("period_start", "")),
            period_end=str(payload.get("period_end", "")),
            currency_symbol=str(payload.get("currency_symbol", "$")),
            raw_text=str(payload.get("raw_text", "")),
            executive_summary=str(payload.get("executive_summary", "")),
            line_items=[
                ParsedLineItem.from_dict(item)
                for item in payload.get("line_items", []) or []
            ],
            insignificant=[str(item) for item in payload.get("insignificant", []) or []],
            gaps=[str(item) for item in payload.get("gaps", []) or []],
            tool_diagnostics=[
                str(item) for item in payload.get("tool_diagnostics", []) or []
            ],
            tool_traces=[
                ToolTrace.from_dict(item)
                for item in payload.get("tool_traces", []) or []
            ],
        )
