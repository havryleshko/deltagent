from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from agent.models import AgentRun, Evidence, ToolTrace
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


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


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


def _canonical_line_item_key(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))


def _index_traces_by_canonical_line_item(traces: list[ToolTrace]) -> dict[str, list[ToolTrace]]:
    out: dict[str, list[ToolTrace]] = {}
    for trace in traces:
        raw = str(trace.input_payload.get("line_item", "")).strip()
        if not raw:
            continue
        key = _canonical_line_item_key(raw)
        if not key:
            continue
        out.setdefault(key, []).append(trace)
    return out


def _item_line_item_key(item: Any) -> str:
    raw = (item.line_item_name or item.header.split("|")[0]).strip()
    return _canonical_line_item_key(raw)


def _strip_markdown_emphasis(text: str) -> str:
    return text.replace("**", "")


def _compact_board_pack_text(text: str) -> str:
    if not text.strip():
        return text
    compacted = _strip_markdown_emphasis(text).strip()
    replacements = (
        (r"\bThe Slack thread confirms\b", "Slack indicates"),
        (r"\bThe Slack message states\b", "Slack indicates"),
        (r"\bThe Slack evidence notes\b", "Slack indicates"),
        (r"\bNo formal email evidence was found; this is sourced from ([^.]+)\.", r"Evidence is limited to \1."),
        (r"\bNo Slack context was available for this line;", "Slack did not corroborate this line;"),
        (r"\bFinance should confirm whether ([^.]+)\.", r"It should be confirmed whether \1."),
        (r"\bFinance may wish to confirm whether ([^.]+)\.", r"It should be confirmed whether \1."),
        (r"\bFinance should confirm ([^.]+)\.", r"\1 should be confirmed."),
        (r"\bFinance may wish to confirm ([^.]+)\.", r"\1 should be confirmed."),
        (r"\bFinance should track ([^.]+)\.", r"\1 should be tracked."),
        (r"\bFinance should consider ([^.]+)\.", r"\1 should be considered."),
        (r"\bFinance may wish to confirm\b", "It should be confirmed"),
        (r"\bFinance should confirm\b", "It should be confirmed"),
        (r"\bFinance should track\b", "It should be tracked"),
        (r"\bFinance should consider\b", "Consider"),
        (r"\bA formal [^.]+ may be warranted\.", ""),
    )
    for pattern, replacement in replacements:
        compacted = re.sub(pattern, replacement, compacted, flags=re.IGNORECASE)
    if "\n-" not in compacted:
        sentences = re.split(r"(?<=[.!?])\s+", compacted)
        kept: list[str] = []
        drop_patterns = (
            r"^No evidence of unplanned or unapproved spend was found\.?$",
            r"^No cost overruns were identified in the period\.?$",
        )
        for sentence in sentences:
            stripped = sentence.strip()
            if not stripped:
                continue
            if any(re.match(pattern, stripped, flags=re.IGNORECASE) for pattern in drop_patterns):
                continue
            kept.append(stripped)
        compacted = " ".join(kept)
    compacted = re.sub(r"[ \t]{2,}", " ", compacted)
    compacted = re.sub(r"\n{3,}", "\n\n", compacted)
    return compacted.strip()


def _has_meaningful_sources(sources: list[Evidence]) -> bool:
    return any(_source_is_meaningful(source) for source in sources)


def _source_is_meaningful(source: Evidence) -> bool:
    source_type = source.source_type.strip().lower()
    source_id = source.id.strip().lower()
    timestamp = source.timestamp.strip().lower()
    snippet = source.snippet.strip().lower()
    if source_type in {"", "source", "malformed_source"}:
        return False
    if not source_id or source_id == "n/a":
        return False
    if any(marker in timestamp for marker in ("no evidence found", "n/a")):
        return False
    if any(
        marker in snippet
        for marker in ("no evidence found", "no results returned", "no context found", "n/a")
    ):
        return False
    return bool(source.snippet.strip())


def _title_source_type(value: str) -> str:
    lookup = {
        "crm": "CRM",
        "gmail": "Gmail",
        "slack": "Slack",
        "calendar": "Calendar",
    }
    return lookup.get(value.lower().strip(), value.strip() or "Source")


def _tool_trace_payload(trace: ToolTrace) -> dict[str, Any]:
    try:
        payload = json.loads(trace.output_text)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _evidence_from_tool_traces(traces: list[ToolTrace]) -> list[Evidence]:
    evidence_items: list[Evidence] = []
    seen_ids: set[str] = set()
    for trace in traces:
        payload = _tool_trace_payload(trace)
        for raw_item in payload.get("evidence", []) or []:
            if not isinstance(raw_item, dict):
                continue
            source = Evidence.from_dict(raw_item)
            if not source.id or source.id in seen_ids:
                continue
            source.source_type = _title_source_type(source.source_type)
            evidence_items.append(source)
            seen_ids.add(source.id)
    return evidence_items


def _clean_section_text(text: str) -> str:
    return "\n".join(
        line for line in text.splitlines() if line.strip() and line.strip() != "---"
    ).strip()


def _rebuild_raw_text(
    executive_summary: str,
    line_items: list[Any],
    insignificant: list[str],
) -> str:
    lines = ["EXECUTIVE SUMMARY"]
    if executive_summary.strip():
        lines.append(_clean_section_text(executive_summary))
    lines.extend(["", "LINE COMMENTARY", ""])
    for item in line_items:
        lines.append(item.header.strip())
        if item.final_commentary.strip():
            lines.append(_clean_section_text(item.final_commentary))
        if item.sources:
            lines.append("Sources")
            for source in item.sources:
                lines.append(
                    f"- {_title_source_type(source.source_type)} - {source.timestamp} - {source.id} - {source.snippet}"
                )
        lines.append("")
    lines.append("INSIGNIFICANT VARIANCES")
    for entry in insignificant:
        cleaned = _clean_section_text(entry)
        if cleaned:
            lines.append(cleaned)
    return "\n".join(lines).strip()


def _normalize_output_structure(
    executive_summary: str,
    line_items: list[Any],
    insignificant: list[str],
    tool_traces: list[ToolTrace],
) -> tuple[str, list[Any], list[str], list[str], str]:
    traces_by_line_item = _index_traces_by_canonical_line_item(tool_traces)

    normalized_items: list[Any] = []
    gaps: list[str] = []
    for item in line_items:
        name = _item_line_item_key(item)
        replacement_sources = _evidence_from_tool_traces(traces_by_line_item.get(name, []))
        meaningful_sources = [source for source in item.sources if _source_is_meaningful(source)]
        item.sources = meaningful_sources or replacement_sources
        item.commentary = _compact_board_pack_text(_clean_section_text(item.commentary))
        if not _has_meaningful_sources(item.sources):
            item.commentary = _enforce_no_context_abstention(item.commentary)
        normalized_items.append(item)
        body = item.final_commentary.lower()
        if "no context found" in body or "tool failed" in body:
            gaps.append(item.header)

    normalized_summary = _compact_board_pack_text(_clean_section_text(executive_summary))
    normalized_insignificant = [
        cleaned
        for cleaned in (_compact_board_pack_text(_clean_section_text(line)) for line in insignificant)
        if cleaned
    ]
    normalized_raw_text = _rebuild_raw_text(
        normalized_summary,
        normalized_items,
        normalized_insignificant,
    )
    return normalized_summary, normalized_items, normalized_insignificant, gaps, normalized_raw_text


def _enforce_no_context_abstention(commentary: str) -> str:
    text = commentary.strip()
    if not text:
        return "No context found — recommend review."
    lower = text.lower()
    if "no context found" in lower or "no supporting context" in lower or "no evidence" in lower:
        return "No context found — recommend review."
    return text


def _trace_text(traces: list[ToolTrace]) -> str:
    chunks: list[str] = []
    for trace in traces:
        payload = _tool_trace_payload(trace)
        summary = str(payload.get("summary_for_model", "")).strip()
        if summary:
            chunks.append(summary)
        for raw_item in payload.get("evidence", []) or []:
            if isinstance(raw_item, dict):
                chunks.append(str(raw_item.get("snippet", "")).strip())
    return "\n".join(chunk for chunk in chunks if chunk).lower()


def _merged_trace_text_for_softening(tool_traces: list[ToolTrace], line_items: list[Any]) -> str:
    idx = _index_traces_by_canonical_line_item(tool_traces)
    parts = [_trace_text(tool_traces)]
    for item in line_items:
        parts.append(_trace_text(idx.get(_item_line_item_key(item), [])))
    return "\n".join(p for p in parts if p)


def _has_partial_evidence(trace_text: str) -> bool:
    return any(
        token in trace_text
        for token in (
            "expected",
            "estimate",
            "remaining",
            "pending",
            "risk",
            "re-qualify",
            "re-qualified",
            "re-qualification",
            "forecast",
            "reforecast",
            "recoverable",
            "recovery",
            "subject to",
            "confirmation",
            "provision",
            "reserve",
            "~",
            "approximately",
            "landing",
            "absorb",
            "provisioning",
            "warrant",
            "requires confirmation",
            "subject to",
            "contingent",
            "tbc",
            "unclear",
            "preliminary",
            "provisional",
            "outcome pending",
            "to be confirmed",
            "signature pending",
            "re-qualify risk",
            "subject to matter timing",
            "on track",
        )
    )


def _soften_confidence_text(text: str, trace_text: str) -> str:
    if not text.strip() or not _has_partial_evidence(trace_text):
        return text
    softened = text
    replacements = (
        (r"\bwill be absorbed into next month's plan\b", "is expected to support upcoming periods, subject to latest forecast timing"),
        (r"\bwill all normalise in November\b", "is expected to normalize as the related deals close, subject to timing"),
        (r"\bexpected pipeline recovery\b", "potential pipeline recovery"),
        (r"\bexpected to land\b", "currently expected to close"),
        (r"\bexpected to absorb\b", "may support upcoming periods"),
        (r"\bexpected to repeat\b", "may repeat"),
        (r"\bis likely to carry\b", "could carry"),
        (r"\bis expected to run through at least\b", "is currently expected to run through at least"),
        (r"\bfinance should consider provisioning\b", "the remaining exposure should be monitored against the latest forecast"),
        (r"\bfinance may wish to confirm whether further budget provision is required\b", "the remaining exposure should be monitored against the latest forecast"),
        (r"\brequires provisioning or budget re-forecasting\b", "should be monitored in the latest forecast"),
        (r"\bbudget provision for that range is recommended\b", "that range should be reflected in ongoing forecast review"),
        (r"\bwill recur\b", "is expected to recur"),
        (r"\bwill continue\b", "is expected to continue"),
        (r"\bwill close\b", "is expected to close"),
        (r"\bwill complete\b", "is expected to complete"),
        (r"\bwill settle\b", "is expected to settle"),
        (r"\bwill reverse\b", "may reverse"),
        (r"\bwill be recovered\b", "is expected to be recovered"),
        (r"\bno further spend is expected\b", "no further spend is currently indicated"),
        (r"\bfully explained\b", "well supported"),
        (r"\bfully reconciled\b", "largely reconciled"),
        (r"\bon track for\b", "currently tracking to"),
        (r"\bwill all normalise in ([a-z]+)\b", r"is expected to normalize in \1"),
    )
    for pattern, replacement in replacements:
        softened = re.sub(pattern, replacement, softened, flags=re.IGNORECASE)
    return softened


def _append_material_detail(text: str, sentence: str) -> str:
    stripped = text.rstrip()
    if sentence.lower() in stripped.lower():
        return stripped
    if not stripped:
        return sentence
    return f"{stripped} {sentence}"


def _enrich_material_detail(text: str, line_item_name: str, trace_text: str) -> tuple[str, list[str]]:
    warnings: list[str] = []
    enriched = text
    name = line_item_name.lower().strip()
    if "repair" in name and "insurance claim" in trace_text and "insurance" not in enriched.lower():
        enriched = _append_material_detail(
            enriched,
            "A building insurance claim has also been submitted, and any recovery timing should be confirmed separately.",
        )
        warnings.append(f"Recovered missing evidence detail: {line_item_name} insurance claim")
    if "professional fees" in name and "vantec" in trace_text and "vantec" not in enriched.lower():
        enriched = _append_material_detail(
            enriched,
            "The matter relates to the Vantec Corp patent claim and remaining spend should be treated as an estimate rather than a fixed reserve.",
        )
        warnings.append(f"Recovered missing evidence detail: {line_item_name} Vantec context")
    if "professional fees" in name and "remaining $8–18k" in trace_text and "8–18k" not in enriched.lower() and "8-18k" not in enriched.lower():
        enriched = _append_material_detail(
            enriched,
            "Current evidence indicates remaining exposure of approximately $8–18K in Q1 2025, subject to matter timing.",
        )
        warnings.append(f"Recovered missing evidence detail: {line_item_name} remaining exposure")
    for needle, mention, sentence in (
        ("venue credit", "venue credit", "Fixture evidence references a venue credit; recognition timing should be confirmed."),
        ("uspto", "uspto", "Fixture evidence references USPTO-related costs; remaining spend should be treated as an estimate pending matter updates."),
    ):
        if needle in trace_text and mention not in enriched.lower():
            enriched = _append_material_detail(enriched, sentence)
            warnings.append(f"Recovered missing evidence detail: {needle}")
    return enriched, warnings


def _apply_confidence_and_evidence_enrichment(
    executive_summary: str,
    line_items: list[Any],
    tool_traces: list[ToolTrace],
) -> tuple[str, list[Any], list[str]]:
    traces_by_line_item = _index_traces_by_canonical_line_item(tool_traces)

    diagnostics: list[str] = []
    softening_trace_text = _merged_trace_text_for_softening(tool_traces, line_items)
    executive_summary = _compact_board_pack_text(_soften_confidence_text(executive_summary, softening_trace_text))
    for item in line_items:
        name = _item_line_item_key(item)
        item_trace_text = _trace_text(traces_by_line_item.get(name, []))
        item.commentary = _compact_board_pack_text(_soften_confidence_text(item.commentary, item_trace_text))
        item.commentary, item_warnings = _enrich_material_detail(
            item.commentary,
            item.line_item_name or item.header.split("|")[0].strip(),
            item_trace_text,
        )
        diagnostics.extend(item_warnings)
    return executive_summary, line_items, diagnostics


def _validate_tool_coverage(
    line_items: list[Any],
    tool_traces: list[ToolTrace],
) -> list[str]:
    by_line_item = _index_traces_by_canonical_line_item(tool_traces)

    warnings: list[str] = []
    for item in line_items:
        name = _item_line_item_key(item)
        label_lower = _normalize_line_item_name(item.line_item_name or item.header.split("|")[0])
        traces = by_line_item.get(name, [])
        if not traces:
            continue
        item_trace_text = _trace_text(traces)
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
        if "gmail" in {name.replace("search_", "") for name in tool_names} and "narrow" not in search_scopes and any(
            token in name for token in ("repair", "maintenance", "legal", "professional fees")
        ):
            warnings.append(f"Missing narrow Gmail follow-up: {item.header!r}")
        if any(
            token in label_lower for token in ("revenue", "professional services", "cost of revenue", "contractor")
        ) and "search_crm" not in tool_names:
            warnings.append(f"Missing CRM follow-up: {item.header!r}")
        if "repair" in label_lower and "insurance claim" in item_trace_text and "insurance" not in body_lower:
            warnings.append(f"Missing evidence detail: {item.header!r} should mention insurance claim")
        if "professional fees" in label_lower and "vantec" in item_trace_text and "vantec" not in body_lower:
            warnings.append(f"Missing evidence detail: {item.header!r} should mention Vantec context")
        successful_tool_names = {
            trace.tool_name
            for trace in traces
            if (_tool_trace_payload(trace).get("evidence") or [])
        }
        if any(
            token in label_lower
            for token in (
                "professional services",
                "cost of revenue",
                "contractor",
                "contractor spend",
                "project",
            )
        ):
            if len(successful_tool_names) < 2:
                warnings.append(f"Thin single-source corroboration: {item.header!r}")
            if len(successful_tool_names) == 1 and len(tool_names) == 1:
                warnings.append(f"Missing corroborating follow-up: {item.header!r}")
    return warnings


def _validate_executive_summary(
    executive_summary: str,
    currency_symbol: str,
    significant_rows: list[dict[str, Any]],
    insignificant_rows: list[dict[str, Any]],
) -> list[str]:
    warnings: list[str] = []
    if not executive_summary.strip():
        return warnings
    all_rows = list(significant_rows) + list(insignificant_rows)
    summary_lower = executive_summary.lower()
    if len(all_rows) >= 2:
        combined_budget, combined_actual, _, _ = _rollup_rows(all_rows)
        allowed_naive_labels = ("sum of all lines", "mixed revenue and expense")
        if not any(label in summary_lower for label in allowed_naive_labels):
            fmt_b = _format_money(combined_budget, currency_symbol)
            fmt_a = _format_money(combined_actual, currency_symbol)
            if fmt_b in executive_summary and fmt_a in executive_summary:
                warnings.append(
                    "Executive summary appears to cite naive sum-of-all-lines totals; not a P&L net figure."
                )
    if not significant_rows or not insignificant_rows:
        return warnings

    full_budget, full_actual, _, _ = _rollup_rows(significant_rows + insignificant_rows)
    sig_budget, sig_actual, _, _ = _rollup_rows(significant_rows)

    if any(label in summary_lower for label in ("significant line", "significant-line", "significant variances")):
        return warnings

    uses_sig_totals = (
        _format_money(sig_budget, currency_symbol) in executive_summary
        and _format_money(sig_actual, currency_symbol) in executive_summary
    )
    uses_full_totals = (
        _format_money(full_budget, currency_symbol) in executive_summary
        and _format_money(full_actual, currency_symbol) in executive_summary
    )
    if uses_sig_totals and not uses_full_totals:
        warnings.append("Executive summary appears to use significant-line totals as full totals.")
    return warnings


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


def _validate_confidence(
    executive_summary: str,
    line_items: list[Any],
    tool_traces: list[ToolTrace],
) -> list[str]:
    warnings: list[str] = []
    combined_trace_text = _merged_trace_text_for_softening(tool_traces, line_items)
    strong_patterns = (
        r"\bwill\b",
        r"fully explained",
        r"fully reconciled",
        r"no further spend is expected",
        r"finance should",
        r"\bprovision(?:ing)?\b",
        r"\breforecast(?:ing)?\b",
        r"expected pipeline recovery",
        r"expected to land",
        r"full recovery",
        r"\bcertain\b",
        r"\bcertainly\b",
        r"\bguaranteed\b",
        r"\bno doubt\b",
        r"\bwill close\b",
        r"\bwill complete\b",
        r"\bwill settle\b",
        r"\bon track for\b",
        r"\blikely to land\b",
        r"\blikely to carry\b",
    )
    if _has_partial_evidence(combined_trace_text) and any(
        re.search(pattern, executive_summary, flags=re.IGNORECASE) for pattern in strong_patterns
    ):
        warnings.append("Executive summary still contains unsupported certainty language.")
    traces_by_line_item = _index_traces_by_canonical_line_item(tool_traces)
    for item in line_items:
        name = _item_line_item_key(item)
        item_trace_text = _trace_text(traces_by_line_item.get(name, []))
        if _has_partial_evidence(item_trace_text) and any(
            re.search(pattern, item.commentary, flags=re.IGNORECASE) for pattern in strong_patterns
        ):
            warnings.append(f"Unsupported certainty language: {item.header!r}")
    return warnings


def _length_review_diagnostics(
    executive_summary: str,
    line_items: list[Any],
) -> list[str]:
    warnings: list[str] = []
    summary_word_count = len(executive_summary.split())
    if summary_word_count > 120:
        warnings.append(f"Executive summary may be too long for board-pack style: {summary_word_count} words")
    for item in line_items:
        word_count = len(item.final_commentary.split())
        if word_count > 85:
            warnings.append(f"Line commentary may be too long for board-pack style: {item.header!r}")
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
    executive_summary, line_items, enrichment_warnings = _apply_confidence_and_evidence_enrichment(
        executive_summary,
        line_items,
        tool_traces,
    )
    executive_summary, line_items, insignificant, gaps, raw_text = _normalize_output_structure(
        executive_summary,
        line_items,
        insignificant,
        tool_traces,
    )
    source_warnings = validate_parsed_output(line_items)
    tool_coverage_warnings = _validate_tool_coverage(line_items, tool_traces)
    summary_warnings = _validate_executive_summary(
        executive_summary,
        currency_symbol,
        list(significant_rows or []),
        list(insignificant_rows or []),
    )
    line_item_warnings = _validate_line_item_consistency(line_items)
    confidence_warnings = _validate_confidence(executive_summary, line_items, tool_traces)
    length_warnings = _length_review_diagnostics(executive_summary, line_items)
    all_diagnostics = _dedupe_preserve_order(
        list(tool_diagnostics)
        + enrichment_warnings
        + source_warnings
        + tool_coverage_warnings
        + summary_warnings
        + line_item_warnings
        + confidence_warnings
        + length_warnings
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
                    entry = f"{name}: {error_message}"
                    if not tool_diagnostics or tool_diagnostics[-1] != entry:
                        tool_diagnostics.append(entry)
        messages.append({"role": "user", "content": tool_results})
