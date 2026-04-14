from __future__ import annotations

from agent.models import AgentRun, Evidence, ParsedLineItem
from evals.oracle_scorer import score_agent_run


def _run(summary: str, line_items: list[ParsedLineItem]) -> AgentRun:
    return AgentRun(
        run_id="run_test",
        period_label="November 2024",
        period_start="2024-11-01T00:00:00Z",
        period_end="2024-11-30T23:59:59Z",
        currency_symbol="$",
        raw_text="",
        executive_summary=summary,
        line_items=line_items,
        insignificant=["- Other: +$10 (+1.0%)"],
    )


def test_supported_line_scores_with_expected_evidence_and_driver():
    oracle = {
        "workbook": "test.xlsx",
        "summary_expectations": {
            "must_surface_lines": ["Revenue"],
            "forbid_mixed_total_story": False,
        },
        "lines": [
            {
                "line_item": "Revenue",
                "budget_usd": 100.0,
                "actual_usd": 120.0,
                "variance_usd": 20.0,
                "significant": True,
                "supported": True,
                "expected_driver_keywords": ["pulled forward", "closed won"],
                "allowed_source_families": ["crm"],
                "expected_evidence_ids": ["crm-revenue-broad"],
            }
        ],
    }
    run = _run(
        "Revenue drove the month.",
        [
            ParsedLineItem(
                header="Revenue | +$20 (+20.0%) | Budget: $100 | Actual: $120",
                commentary="Revenue was pulled forward from deals that moved to closed won.",
                sources=[
                    Evidence(
                        id="crm-revenue-broad",
                        source_type="CRM",
                        timestamp="2024-11-07",
                        snippet="Deals moved to closed won.",
                    )
                ],
                line_item_name="Revenue",
                budget_usd=100.0,
                actual_usd=120.0,
                variance_usd=20.0,
            )
        ],
    )

    result = score_agent_run(run, oracle)

    assert result["metrics"]["supported_line_recall"] == 1.0
    assert result["metrics"]["driver_accuracy"] == 1.0
    assert result["breakdown"]["significant_line_truthfulness"] > 30


def test_placeholder_sources_do_not_count_as_evidence():
    oracle = {
        "workbook": "test.xlsx",
        "summary_expectations": {
            "must_surface_lines": ["Property Insurance"],
            "forbid_mixed_total_story": False,
        },
        "lines": [
            {
                "line_item": "Property Insurance",
                "budget_usd": 100.0,
                "actual_usd": 115.0,
                "variance_usd": 15.0,
                "significant": True,
                "supported": False,
            }
        ],
    }
    run = _run(
        "Property Insurance needs review.",
        [
            ParsedLineItem(
                header="Property Insurance | +$15 (+15.0%) | Budget: $100 | Actual: $115",
                commentary="This may reflect a renewal increase. No context found — recommend review.",
                sources=[
                    Evidence(
                        id="N/A",
                        source_type="Gmail",
                        timestamp="No evidence found",
                        snippet="No results returned (broad and narrow)",
                    )
                ],
                line_item_name="Property Insurance",
                budget_usd=100.0,
                actual_usd=115.0,
                variance_usd=15.0,
            )
        ],
    )

    result = score_agent_run(run, oracle)
    line_result = result["line_results"][0]

    assert result["metrics"]["unsupported_line_precision"] == 0.0
    assert line_result["placeholder_sources"] is True
    assert line_result["invented_specifics"] is True


def test_summary_usefulness_penalizes_mixed_total_story():
    oracle = {
        "workbook": "test.xlsx",
        "summary_expectations": {
            "must_surface_lines": ["Revenue", "Salaries"],
            "forbid_mixed_total_story": True,
        },
        "lines": [],
    }
    run = _run(
        "November closed at $220 against a $200 budget, driven by a revenue beat and salary overrun.",
        [],
    )

    result = score_agent_run(run, oracle)

    assert result["metrics"]["summary_usefulness"] < 0.7
