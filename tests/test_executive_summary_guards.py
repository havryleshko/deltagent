from __future__ import annotations

from agent.agent import _validate_executive_summary


def test_warns_when_naive_sum_budget_and_actual_in_summary():
    significant = [
        {
            "line_item": "Revenue",
            "budget_usd": 100_000.0,
            "actual_usd": 110_000.0,
            "variance_usd": 10_000.0,
            "variance_pct": 10.0,
        }
    ]
    insignificant = [
        {
            "line_item": "Salaries",
            "budget_usd": 50_000.0,
            "actual_usd": 48_000.0,
            "variance_usd": -2_000.0,
            "variance_pct": -4.0,
        }
    ]
    summary = "Period closed at $150,000 budget versus $158,000 actual."
    warnings = _validate_executive_summary(summary, "$", significant, insignificant)
    assert any("naive sum-of-all-lines" in w for w in warnings)


def test_allowed_label_suppresses_naive_warning():
    significant = [
        {
            "line_item": "Revenue",
            "budget_usd": 100_000.0,
            "actual_usd": 110_000.0,
            "variance_usd": 10_000.0,
            "variance_pct": 10.0,
        }
    ]
    insignificant = [
        {
            "line_item": "Salaries",
            "budget_usd": 50_000.0,
            "actual_usd": 48_000.0,
            "variance_usd": -2_000.0,
            "variance_pct": -4.0,
        }
    ]
    summary = (
        "Mixed revenue and expense: $150,000 budget versus $158,000 actual across all lines."
    )
    warnings = _validate_executive_summary(summary, "$", significant, insignificant)
    assert not any("naive sum-of-all-lines" in w for w in warnings)


def test_single_row_skips_naive_check():
    significant = [
        {
            "line_item": "Revenue",
            "budget_usd": 100_000.0,
            "actual_usd": 110_000.0,
            "variance_usd": 10_000.0,
            "variance_pct": 10.0,
        }
    ]
    summary = "Budget $100,000 and actual $110,000."
    warnings = _validate_executive_summary(summary, "$", significant, [])
    assert not any("naive sum-of-all-lines" in w for w in warnings)
