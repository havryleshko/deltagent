from __future__ import annotations

import asyncio
import json
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agent.agent import _fallback_run, _gaps_from_diagnostics
from agent.models import AgentRun, ToolTrace
from agent.parser import parse_agent_output, validate_parsed_output
from cli import app

FIXTURE_CSV = Path(__file__).parent / "fixtures" / "sample_november_2024.csv"
runner = CliRunner()


def test_cli_validate_success() -> None:
    result = runner.invoke(app, ["validate", str(FIXTURE_CSV), "--period", "2024-11"])
    assert result.exit_code == 0
    assert "CSV validation passed." in result.stdout


def test_cli_run_dry_run_prints_plan() -> None:
    result = runner.invoke(
        app,
        ["run", str(FIXTURE_CSV), "--period", "2024-11", "--dry-run"],
    )
    assert result.exit_code == 0
    assert "Bounds:" in result.stdout
    assert "Revenue:" in result.stdout


def test_parser_extracts_sources_and_gaps() -> None:
    text = """EXECUTIVE SUMMARY
Summary

LINE COMMENTARY

Revenue | Budget: $100 | Actual: $120 | Variance: +$20 (+20%)
Outperformance came from two pulled-forward deals.
Sources
- gmail - 2024-11-10T10:00:00Z - gmail-1 - Approval thread

Professional Fees | Budget: $8 | Actual: $14 | Variance: +$6 (+75%)
No context found — recommend review

INSIGNIFICANT VARIANCES
Software: small.
"""
    executive_summary, line_items, insignificant, gaps = parse_agent_output(text)
    assert executive_summary == "Summary"
    assert len(line_items) == 2
    assert line_items[0].sources[0].id == "gmail-1"
    assert insignificant == ["Software: small."]
    assert gaps == ["Professional Fees | Budget: $8 | Actual: $14 | Variance: +$6 (+75%)"]


def test_agent_run_json_round_trip() -> None:
    payload = {
        "run_id": "run_20240101_000000",
        "period_label": "November 2024",
        "period_start": "2024-11-01T00:00:00Z",
        "period_end": "2024-11-30T23:59:59Z",
        "currency_symbol": "$",
        "raw_text": "EXECUTIVE SUMMARY\nSummary",
        "executive_summary": "Summary",
        "line_items": [],
        "insignificant": [],
        "gaps": [],
        "tool_diagnostics": [],
        "tool_traces": [],
    }
    restored = AgentRun.from_dict(json.loads(json.dumps(payload)))
    assert restored.to_dict()["period_label"] == "November 2024"


def test_cli_validate_bad_file_exits_nonzero(tmp_path: Path) -> None:
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("not,valid,headers\n1,2,3\n", encoding="utf-8")
    result = runner.invoke(app, ["validate", str(bad_csv)])
    assert result.exit_code == 1
    assert result.stdout.strip()


def test_cli_validate_missing_file_exits_nonzero() -> None:
    result = runner.invoke(app, ["validate", "/nonexistent/path/data.csv"])
    assert result.exit_code != 0


def test_validate_parsed_output_missing_sources_returns_warning() -> None:
    text = """EXECUTIVE SUMMARY
Summary

LINE COMMENTARY

Revenue | Budget: $100 | Actual: $120 | Variance: +$20 (+20%)
Outperformance from pulled-forward deals.

INSIGNIFICANT VARIANCES
"""
    _, line_items, _, _ = parse_agent_output(text)
    warnings = validate_parsed_output(line_items)
    assert len(warnings) == 1
    assert "Revenue" in warnings[0]


def test_validate_parsed_output_no_evidence_marker_is_ok() -> None:
    text = """EXECUTIVE SUMMARY
Summary

LINE COMMENTARY

Professional Fees | Budget: $8 | Actual: $14 | Variance: +$6 (+75%)
No context found — recommend review

INSIGNIFICANT VARIANCES
"""
    _, line_items, _, _ = parse_agent_output(text)
    warnings = validate_parsed_output(line_items)
    assert warnings == []


def test_validate_parsed_output_with_sources_is_ok() -> None:
    text = """EXECUTIVE SUMMARY
Summary

LINE COMMENTARY

Revenue | Budget: $100 | Actual: $120 | Variance: +$20 (+20%)
Outperformance from pulled-forward deals.
Sources
- gmail - 2024-11-10T10:00:00Z - gmail-1 - Approval thread

INSIGNIFICANT VARIANCES
"""
    _, line_items, _, _ = parse_agent_output(text)
    warnings = validate_parsed_output(line_items)
    assert warnings == []


def test_validate_parsed_output_placeholder_sources_returns_warning() -> None:
    text = """EXECUTIVE SUMMARY
Summary

LINE COMMENTARY

Revenue | Budget: $100 | Actual: $120 | Variance: +$20 (+20%)
Outperformance from pulled-forward deals.
Sources
- gmail

INSIGNIFICANT VARIANCES
"""
    _, line_items, _, _ = parse_agent_output(text)
    warnings = validate_parsed_output(line_items)
    assert warnings == ["Malformed or placeholder sources: 'Revenue | Budget: $100 | Actual: $120 | Variance: +$20 (+20%)'"]


def test_parser_source_line_allows_hyphens_in_snippet() -> None:
    text = """EXECUTIVE SUMMARY
Summary

LINE COMMENTARY

Revenue | Budget: $100 | Actual: $120 | Variance: +$20 (+20%)
Outperformance from pulled-forward deals.
Sources
- gmail - 2024-11-10T10:00:00Z - gmail-1 - Approval thread - moved deal close by one week

INSIGNIFICANT VARIANCES
"""
    _, line_items, _, _ = parse_agent_output(text)
    assert line_items[0].sources[0].snippet == "Approval thread - moved deal close by one week"


def test_gaps_from_diagnostics_produces_gap_entries() -> None:
    diagnostics = ["search_gmail: connection timeout", "search_crm: 403 Forbidden"]
    gaps = _gaps_from_diagnostics(diagnostics)
    assert "tool error: search_gmail" in gaps
    assert "tool error: search_crm" in gaps


def test_fallback_run_merges_gaps_from_diagnostics() -> None:
    text = """EXECUTIVE SUMMARY
Summary

LINE COMMENTARY

Revenue | Budget: $100 | Actual: $120 | Variance: +$20 (+20%)
No context found — recommend review

INSIGNIFICANT VARIANCES
"""
    run = _fallback_run(
        period_label="November 2024",
        period_start="2024-11-01T00:00:00Z",
        period_end="2024-11-30T23:59:59Z",
        currency_symbol="$",
        raw_text=text,
        tool_diagnostics=["search_slack: timeout"],
        tool_traces=[],
    )
    assert any("Revenue" in g for g in run.gaps)
    assert any("search_slack" in g for g in run.gaps)


def test_fallback_run_warns_on_significant_line_totals_in_executive_summary() -> None:
    text = """EXECUTIVE SUMMARY
November closed with actual spend of $120 versus budget of $100.

LINE COMMENTARY

Revenue | Budget: $100 | Actual: $120 | Variance: +$20 (+20%)
Outperformance from pulled-forward deals.
Sources
- gmail - 2024-11-10T10:00:00Z - gmail-1 - Approval thread

INSIGNIFICANT VARIANCES
Software: small.
"""
    run = _fallback_run(
        period_label="November 2024",
        period_start="2024-11-01T00:00:00Z",
        period_end="2024-11-30T23:59:59Z",
        currency_symbol="$",
        raw_text=text,
        tool_diagnostics=[],
        tool_traces=[],
        significant_rows=[
            {
                "period": "November 2024",
                "line_item": "Revenue",
                "budget_usd": 100.0,
                "actual_usd": 120.0,
                "variance_usd": 20.0,
                "variance_pct": 20.0,
            }
        ],
        insignificant_rows=[
            {
                "period": "November 2024",
                "line_item": "Software",
                "budget_usd": 50.0,
                "actual_usd": 70.0,
                "variance_usd": 20.0,
                "variance_pct": 40.0,
            }
        ],
    )
    assert "Executive summary appears to use significant-line totals as full totals." in run.tool_diagnostics


def test_fallback_run_warns_on_commentary_percent_mismatch() -> None:
    text = """EXECUTIVE SUMMARY
Summary

LINE COMMENTARY

Repairs Maintenance | Budget: $100 | Actual: $886 | Variance: +$786 (+786.3%)
This represents 886% overspend against budget.
Sources
- gmail - 2024-11-10T10:00:00Z - gmail-1 - Invoice thread

INSIGNIFICANT VARIANCES
"""
    run = _fallback_run(
        period_label="November 2024",
        period_start="2024-11-01T00:00:00Z",
        period_end="2024-11-30T23:59:59Z",
        currency_symbol="$",
        raw_text=text,
        tool_diagnostics=[],
        tool_traces=[],
        significant_rows=[
            {
                "period": "November 2024",
                "line_item": "Repairs Maintenance",
                "budget_usd": 100.0,
                "actual_usd": 886.0,
                "variance_usd": 786.0,
                "variance_pct": 786.3,
            }
        ],
        insignificant_rows=[],
    )
    assert any("Percent mismatch in commentary" in warning for warning in run.tool_diagnostics)


def test_fallback_run_rebuilds_canonical_sources_from_tool_traces() -> None:
    text = """EXECUTIVE SUMMARY
Summary
---

LINE COMMENTARY

Revenue | +$20 (+20.0%) | Budget: $100 | Actual: $120
Closed one deal early.
Sources:
- CRM — 2024-11-10 — crm-1 — Closed Won

INSIGNIFICANT VARIANCES
Software: small.
"""
    run = _fallback_run(
        period_label="November 2024",
        period_start="2024-11-01T00:00:00Z",
        period_end="2024-11-30T23:59:59Z",
        currency_symbol="$",
        raw_text=text,
        tool_diagnostics=[],
        tool_traces=[
            ToolTrace(
                tool_name="search_crm",
                tool_use_id="toolu_1",
                input_payload={"period": "November 2024", "line_item": "Revenue", "search_scope": "broad"},
                output_text=json.dumps(
                    {
                        "evidence": [
                            {
                                "id": "crm-1",
                                "source_type": "crm",
                                "timestamp": "2024-11-10",
                                "snippet": "Closed Won",
                                "ref": "",
                            }
                        ]
                    }
                ),
            )
        ],
        significant_rows=[
            {
                "period": "November 2024",
                "line_item": "Revenue",
                "budget_usd": 100.0,
                "actual_usd": 120.0,
                "variance_usd": 20.0,
                "variance_pct": 20.0,
            }
        ],
        insignificant_rows=[],
    )
    assert "Sources\n- CRM - 2024-11-10 - crm-1 - Closed Won" in run.raw_text
    assert run.tool_diagnostics == []


def test_fallback_run_drops_placeholder_no_evidence_source_rows() -> None:
    text = """EXECUTIVE SUMMARY
Summary
---

LINE COMMENTARY

Subscriptions | -$1,200 (-100.0%) | Budget: $1,200 | Actual: $0
No context found — recommend review.
Sources:
- Slack (broad) — No evidence returned.
- Gmail (narrow) — No evidence returned.

INSIGNIFICANT VARIANCES
"""
    run = _fallback_run(
        period_label="February 2026",
        period_start="2026-02-01T00:00:00Z",
        period_end="2026-02-28T23:59:59Z",
        currency_symbol="$",
        raw_text=text,
        tool_diagnostics=[],
        tool_traces=[],
        significant_rows=[
            {
                "period": "February 2026",
                "line_item": "Subscriptions",
                "budget_usd": 1200.0,
                "actual_usd": 0.0,
                "variance_usd": -1200.0,
                "variance_pct": -100.0,
            }
        ],
        insignificant_rows=[],
    )
    assert "No evidence returned" not in run.raw_text
    assert "Sources" not in run.raw_text
    assert run.tool_diagnostics == []


def test_fallback_run_softens_unsupported_certainty_language() -> None:
    text = """EXECUTIVE SUMMARY
The miss will be absorbed into next month's plan.

LINE COMMENTARY

Revenue | -$82,000 (-16.4%) | Budget: $500,000 | Actual: $418,000
Three slipped deals will all normalise in November.
Sources
- CRM - 2024-11-07 - crm-1 - Summit is a re-qualify risk and November plan needs to absorb the slips.

INSIGNIFICANT VARIANCES
"""
    run = _fallback_run(
        period_label="October 2024",
        period_start="2024-10-01T00:00:00Z",
        period_end="2024-10-31T23:59:59Z",
        currency_symbol="$",
        raw_text=text,
        tool_diagnostics=[],
        tool_traces=[
            ToolTrace(
                tool_name="search_crm",
                tool_use_id="toolu_2",
                input_payload={"period": "October 2024", "line_item": "Revenue", "search_scope": "broad"},
                output_text=json.dumps(
                    {
                        "summary_for_model": "Summit is a re-qualify risk and November plan needs to absorb the slips.",
                        "evidence": [
                            {
                                "id": "crm-1",
                                "source_type": "crm",
                                "timestamp": "2024-11-07",
                                "snippet": "Summit is a re-qualify risk and November plan needs to absorb the slips.",
                                "ref": "",
                            }
                        ],
                    }
                ),
            )
        ],
        significant_rows=[
            {
                "period": "October 2024",
                "line_item": "Revenue",
                "budget_usd": 500000.0,
                "actual_usd": 418000.0,
                "variance_usd": -82000.0,
                "variance_pct": -16.4,
            }
        ],
        insignificant_rows=[],
    )
    assert "will be absorbed" not in run.raw_text.lower()
    assert "will all normalise" not in run.raw_text.lower()
    assert "expected to support upcoming periods" in run.raw_text.lower()


def test_fallback_run_recovers_missing_insurance_claim_detail() -> None:
    text = """EXECUTIVE SUMMARY
Summary

LINE COMMENTARY

Repairs Maintenance | +$786 (+786.3%) | Budget: $100 | Actual: $886
Emergency repair completed and approved.
Sources
- Gmail - 2024-11-10 - gmail-1 - Emergency repair invoice

INSIGNIFICANT VARIANCES
"""
    run = _fallback_run(
        period_label="February 2026",
        period_start="2026-02-01T00:00:00Z",
        period_end="2026-02-28T23:59:59Z",
        currency_symbol="$",
        raw_text=text,
        tool_diagnostics=[],
        tool_traces=[
            ToolTrace(
                tool_name="search_gmail",
                tool_use_id="toolu_3",
                input_payload={"period": "February 2026", "line_item": "Repairs Maintenance", "search_scope": "narrow"},
                output_text=json.dumps(
                    {
                        "summary_for_model": "Building insurance claim submitted — outcome pending but expense recognised in February.",
                        "evidence": [
                            {
                                "id": "gmail-claim",
                                "source_type": "gmail",
                                "timestamp": "2024-11-10",
                                "snippet": "Building insurance claim submitted — outcome pending but expense recognised in February.",
                                "ref": "",
                            }
                        ],
                    }
                ),
            )
        ],
        significant_rows=[
            {
                "period": "February 2026",
                "line_item": "Repairs Maintenance",
                "budget_usd": 100.0,
                "actual_usd": 886.0,
                "variance_usd": 786.0,
                "variance_pct": 786.3,
            }
        ],
        insignificant_rows=[],
    )
    assert "insurance claim" in run.raw_text.lower()
    assert any("Recovered missing evidence detail" in warning for warning in run.tool_diagnostics)


def test_review_command_saves_state(tmp_path: Path) -> None:
    run = AgentRun.from_dict({
        "run_id": "run_test",
        "period_label": "November 2024",
        "period_start": "",
        "period_end": "",
        "currency_symbol": "$",
        "raw_text": "EXECUTIVE SUMMARY\nSummary\n\nLINE COMMENTARY\n\n"
                    "Revenue | Budget: $100 | Actual: $120 | Variance: +$20 (+20%)\n"
                    "Outperformance.\nSources\n- gmail - 2024-11-10 - g1 - Thread\n\n"
                    "INSIGNIFICANT VARIANCES\n",
        "executive_summary": "Summary",
        "line_items": [
            {
                "header": "Revenue | Budget: $100 | Actual: $120 | Variance: +$20 (+20%)",
                "commentary": "Outperformance.",
                "sources": [{"id": "g1", "source_type": "gmail", "timestamp": "2024-11-10", "snippet": "Thread", "ref": ""}],
                "review_status": "pending",
                "edited_commentary": None,
                "flagged_reason": None,
            }
        ],
        "insignificant": [],
        "gaps": [],
        "tool_diagnostics": [],
        "tool_traces": [],
    })
    run_file = tmp_path / "run_test.json"
    run_file.write_text(json.dumps(run.to_dict()), encoding="utf-8")
    result = runner.invoke(app, ["review", str(run_file)], input="a\n")
    assert result.exit_code == 0
    saved = AgentRun.from_dict(json.loads(run_file.read_text()))
    assert saved.line_items[0].review_status == "accepted"


def test_review_skip_leaves_pending(tmp_path: Path) -> None:
    run = AgentRun.from_dict({
        "run_id": "run_test2",
        "period_label": "November 2024",
        "period_start": "",
        "period_end": "",
        "currency_symbol": "$",
        "raw_text": "",
        "executive_summary": "",
        "line_items": [
            {
                "header": "Salaries | Budget: $50 | Actual: $55 | Variance: +$5 (+10%)",
                "commentary": "Headcount increase.",
                "sources": [],
                "review_status": "pending",
                "edited_commentary": None,
                "flagged_reason": None,
            }
        ],
        "insignificant": [],
        "gaps": [],
        "tool_diagnostics": [],
        "tool_traces": [],
    })
    run_file = tmp_path / "run_test2.json"
    run_file.write_text(json.dumps(run.to_dict()), encoding="utf-8")
    result = runner.invoke(app, ["review", str(run_file)], input="s\n")
    assert result.exit_code == 0
    saved = AgentRun.from_dict(json.loads(run_file.read_text()))
    assert saved.line_items[0].review_status == "pending"
