from __future__ import annotations

import asyncio
import json
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


def _enrich_line_items(
    line_items: list[Any],
    significant_rows: list[dict[str, Any]],
) -> None:
    """Populate numeric fields on each ParsedLineItem by matching to canonical rows."""
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
) -> AgentRun:
    executive_summary, line_items, insignificant, gaps = parse_agent_output(raw_text)
    if significant_rows:
        _enrich_line_items(line_items, significant_rows)
    source_warnings = validate_parsed_output(line_items)
    all_diagnostics = list(tool_diagnostics) + source_warnings
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
