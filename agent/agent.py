from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from agent.models import AgentRun, ToolTrace
from agent.parser import parse_agent_output, validate_parsed_output
from agent.prompts import build_system_prompt, build_user_message
from tools.definitions import TOOL_DEFINITIONS


ToolHandler = Callable[[dict[str, Any]], Awaitable[str]]


def _block_value(block: Any, key: str, default: Any = None) -> Any:
    if isinstance(block, dict):
        return block.get(key, default)
    return getattr(block, key, default)


async def _execute_tool_call(
    tool_call: Any, tool_registry: dict[str, ToolHandler]
) -> tuple[dict[str, Any], ToolTrace]:
    tool_name = _block_value(tool_call, "name", "")
    tool_use_id = _block_value(tool_call, "id", "")
    tool_input = dict(_block_value(tool_call, "input", {}) or {})
    handler = tool_registry.get(tool_name)
    if handler is None:
        content = f"Tool not found: {tool_name}"
    else:
        try:
            content = await handler(tool_input)
            if not isinstance(content, str):
                content = str(content)
        except Exception as error:
            content = f"Tool error ({tool_name}): {error}"
    return (
        {"type": "tool_result", "tool_use_id": tool_use_id, "content": content},
        ToolTrace(
            tool_name=tool_name,
            tool_use_id=tool_use_id,
            input_payload=tool_input,
            output_text=content,
        ),
    )


def _extract_text(response: Any) -> str:
    content = getattr(response, "content", []) or []
    text_blocks = []
    for block in content:
        if _block_value(block, "type") == "text":
            text_value = _block_value(block, "text", "")
            if text_value:
                text_blocks.append(text_value)
    return "\n".join(text_blocks).strip()


def _tool_result_error(content: str) -> str | None:
    if content.startswith("Tool error") or content.startswith("Tool not found"):
        return content
    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        return None
    error = payload.get("error")
    summary = payload.get("summary_for_model", "")
    if error:
        return f"{error}: {summary}"
    return None


def _new_run_id() -> str:
    return datetime.now(timezone.utc).strftime("run_%Y%m%d_%H%M%S")


def _gaps_from_diagnostics(diagnostics: list[str]) -> list[str]:
    gaps: list[str] = []
    for entry in diagnostics:
        tool_name = entry.split(":")[0].strip()
        if tool_name:
            gaps.append(f"tool error: {tool_name}")
    return gaps


def _format_money(value: float, currency_symbol: str) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}{currency_symbol}{abs(value):,.0f}"


def _rollup_rows(rows: list[dict[str, Any]]) -> tuple[float, float, float, float]:
    budget = sum(float(row.get("budget_usd", 0) or 0) for row in rows)
    actual = sum(float(row.get("actual_usd", 0) or 0) for row in rows)
    variance = sum(float(row.get("variance_usd", 0) or 0) for row in rows)
    variance_pct = (variance / abs(budget) * 100) if budget else 0.0
    return budget, actual, variance, variance_pct


def _normalize_line_item_name(value: str) -> str:
    return value.lower().strip()


def _validate_tool_coverage(
    line_items: list[Any],
    tool_traces: list[ToolTrace],
) -> list[str]:
    by_line_item: dict[str, list[ToolTrace]] = {}
    for trace in tool_traces:
        line_item = str(trace.input_payload.get("line_item", "")).strip()
        if not line_item:
            continue
        by_line_item.setdefault(_normalize_line_item_name(line_item), []).append(trace)

    warnings: list[str] = []
    for item in line_items:
        name = _normalize_line_item_name(item.line_item_name or item.header.split("|")[0])
        traces = by_line_item.get(name, [])
        if not traces:
            continue
        search_scopes = {
            str(trace.input_payload.get("search_scope", "broad")).strip().lower()
            for trace in traces
        }
        tool_names = {trace.tool_name for trace in traces}
        body_lower = item.final_commentary.lower()
        if "narrow" not in search_scopes and (
            "no context found" in body_lower or "inferred" in body_lower
        ):
            warnings.append(f"Missing narrow follow-up: {item.header!r}")
        if any(
            token in name for token in ("revenue", "professional services", "cost of revenue", "contractor")
        ) and "search_crm" not in tool_names:
            warnings.append(f"Missing CRM follow-up: {item.header!r}")
    return warnings


def _validate_executive_summary(
    executive_summary: str,
    currency_symbol: str,
    significant_rows: list[dict[str, Any]],
    insignificant_rows: list[dict[str, Any]],
) -> list[str]:
    if not executive_summary.strip():
        return []
    if not significant_rows or not insignificant_rows:
        return []

    full_budget, full_actual, _, _ = _rollup_rows(significant_rows + insignificant_rows)
    sig_budget, sig_actual, _, _ = _rollup_rows(significant_rows)
    summary_lower = executive_summary.lower()

    if any(label in summary_lower for label in ("significant line", "significant-line", "significant variances")):
        return []

    uses_sig_totals = (
        _format_money(sig_budget, currency_symbol) in executive_summary
        and _format_money(sig_actual, currency_symbol) in executive_summary
    )
    uses_full_totals = (
        _format_money(full_budget, currency_symbol) in executive_summary
        and _format_money(full_actual, currency_symbol) in executive_summary
    )
    if uses_sig_totals and not uses_full_totals:
        return ["Executive summary appears to use significant-line totals as full totals."]
    return []


def _validate_line_item_consistency(line_items: list[Any]) -> list[str]:
    warnings: list[str] = []
    for item in line_items:
        if item.variance_pct is None:
            continue
        percentages = re.findall(r"([+-]?\d+(?:,\d{3})*(?:\.\d+)?)%", item.commentary)
        if len(percentages) != 1:
            continue
        body_pct = abs(float(percentages[0].replace(",", "")))
        expected_pct = abs(float(item.variance_pct))
        if abs(body_pct - expected_pct) > 1.0:
            warnings.append(f"Percent mismatch in commentary: {item.header!r}")
    return warnings


def _enrich_line_items(
    line_items: list[Any],
    significant_rows: list[dict[str, Any]],
) -> None:
    row_by_name = {
        str(r.get("line_item", "")).lower().strip(): r for r in significant_rows
    }
    for item in line_items:
        name = item.header.split("|")[0].strip().lower()
        row = row_by_name.get(name)
        if row:
            item.line_item_name = str(row.get("line_item", ""))
            item.budget_usd = row.get("budget_usd")
            item.actual_usd = row.get("actual_usd")
            item.variance_usd = row.get("variance_usd")
            item.variance_pct = row.get("variance_pct")


def _fallback_run(
    *,
    period_label: str,
    period_start: str,
    period_end: str,
    currency_symbol: str,
    raw_text: str,
    tool_diagnostics: list[str],
    tool_traces: list[ToolTrace],
    significant_rows: list[dict[str, Any]] | None = None,
    insignificant_rows: list[dict[str, Any]] | None = None,
) -> AgentRun:
    executive_summary, line_items, insignificant, gaps = parse_agent_output(raw_text)
    if significant_rows:
        _enrich_line_items(line_items, significant_rows)
    source_warnings = validate_parsed_output(line_items)
    tool_coverage_warnings = _validate_tool_coverage(line_items, tool_traces)
    summary_warnings = _validate_executive_summary(
        executive_summary,
        currency_symbol,
        list(significant_rows or []),
        list(insignificant_rows or []),
    )
    line_item_warnings = _validate_line_item_consistency(line_items)
    all_diagnostics = (
        list(tool_diagnostics)
        + source_warnings
        + tool_coverage_warnings
        + summary_warnings
        + line_item_warnings
    )
    extra_gaps = _gaps_from_diagnostics(tool_diagnostics)
    merged_gaps = list(dict.fromkeys(gaps + extra_gaps))
    return AgentRun(
        run_id=_new_run_id(),
        period_label=period_label,
        period_start=period_start,
        period_end=period_end,
        currency_symbol=currency_symbol,
        raw_text=raw_text,
        executive_summary=executive_summary,
        line_items=line_items,
        insignificant=insignificant,
        gaps=merged_gaps,
        tool_diagnostics=all_diagnostics,
        tool_traces=list(tool_traces),
    )


async def run_agent(
    significant_rows: list[dict[str, Any]],
    insignificant_rows: list[dict[str, Any]],
    client: Any | None = None,
    tool_registry: dict[str, ToolHandler] | None = None,
    model: str = "claude-sonnet-4-6",
    max_rounds: int = 8,
    tool_diagnostics: list[str] | None = None,
    currency_symbol: str = "$",
    period_bounds: tuple[str, str] | None = None,
    dry_run: bool = False,
) -> AgentRun:
    tool_registry = tool_registry or {}
    diagnostics = tool_diagnostics if tool_diagnostics is not None else []
    period_label = (
        significant_rows[0]["period"]
        if significant_rows
        else (insignificant_rows[0]["period"] if insignificant_rows else "Unknown Period")
    )
    period_start = period_bounds[0] if period_bounds else ""
    period_end = period_bounds[1] if period_bounds else ""
    tool_traces: list[ToolTrace] = []
    if dry_run:
        return _fallback_run(
            period_label=period_label,
            period_start=period_start,
            period_end=period_end,
            currency_symbol=currency_symbol,
            raw_text="Dry run only.",
            tool_diagnostics=list(diagnostics),
            tool_traces=tool_traces,
            significant_rows=list(significant_rows),
            insignificant_rows=list(insignificant_rows),
        )
    if client is None:
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic()

    messages: list[dict[str, Any]] = [
        {
            "role": "user",
            "content": build_user_message(
                significant_rows=significant_rows,
                insignificant_rows=insignificant_rows,
                currency_symbol=currency_symbol,
                period_start=period_start,
                period_end=period_end,
            ),
        }
    ]

    tools: list[dict[str, Any]] = [
        definition
        for definition in TOOL_DEFINITIONS
        if definition["name"] in tool_registry
    ]

    rounds = 0
    while True:
        rounds += 1
        if rounds > max_rounds:
            return _fallback_run(
                period_label=period_label,
                period_start=period_start,
                period_end=period_end,
                currency_symbol=currency_symbol,
                raw_text="No context found — recommend review",
                tool_diagnostics=list(diagnostics),
                tool_traces=tool_traces,
                significant_rows=list(significant_rows),
                insignificant_rows=list(insignificant_rows),
            )

        response = await client.messages.create(
            model=model,
            max_tokens=4096,
            system=build_system_prompt(),
            messages=messages,
            tools=tools,
        )

        assistant_content = getattr(response, "content", []) or []
        messages.append({"role": "assistant", "content": assistant_content})

        stop_reason = getattr(response, "stop_reason", None)
        if stop_reason != "tool_use":
            text = _extract_text(response)
            raw_text = text or "No context found — recommend review"
            return _fallback_run(
                period_label=period_label,
                period_start=period_start,
                period_end=period_end,
                currency_symbol=currency_symbol,
                raw_text=raw_text,
                tool_diagnostics=list(diagnostics),
                tool_traces=tool_traces,
                significant_rows=list(significant_rows),
                insignificant_rows=list(insignificant_rows),
            )

        tool_calls = [
            block for block in assistant_content if _block_value(block, "type") == "tool_use"
        ]
        if not tool_calls:
            return _fallback_run(
                period_label=period_label,
                period_start=period_start,
                period_end=period_end,
                currency_symbol=currency_symbol,
                raw_text="No context found — recommend review",
                tool_diagnostics=list(diagnostics),
                tool_traces=tool_traces,
                significant_rows=list(significant_rows),
                insignificant_rows=list(insignificant_rows),
            )

        tool_batches = await asyncio.gather(
            *[_execute_tool_call(tool_call, tool_registry) for tool_call in tool_calls]
        )
        tool_results = [item[0] for item in tool_batches]
        tool_traces.extend(item[1] for item in tool_batches)
        if tool_diagnostics is not None:
            for tool_call, result in zip(tool_calls, tool_results):
                content = result.get("content", "")
                error_message = _tool_result_error(content) if isinstance(content, str) else None
                if error_message:
                    name = _block_value(tool_call, "name", "unknown")
                    tool_diagnostics.append(f"{name}: {error_message}")
        messages.append({"role": "user", "content": tool_results})
