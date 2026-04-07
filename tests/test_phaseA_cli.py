from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agent.models import AgentRun
from agent.parser import parse_agent_output
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
