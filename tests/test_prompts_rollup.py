from __future__ import annotations

from agent.prompts import build_user_message


def _row(line: str, budget: float, actual: float, variance: float, pct: float) -> dict:
    return {
        "line_item": line,
        "period": "November 2024",
        "budget_usd": budget,
        "actual_usd": actual,
        "variance_usd": variance,
        "variance_pct": pct,
    }


def test_mixed_pl_emits_revenue_and_expense_buckets_no_full_report_line():
    significant = [
        _row("Revenue", 100_000, 110_000, 10_000, 10.0),
        _row("Salaries", 50_000, 55_000, 5_000, 10.0),
    ]
    insignificant = [_row("Software & Subscriptions", 5_000, 4_900, -100, -2.0)]
    text = build_user_message(significant, insignificant)
    assert "Full report totals" not in text
    assert "Revenue (reported lines) totals:" in text
    assert "Expense (reported lines) totals:" in text
    assert "Do not state a single consolidated" not in text


def test_expense_only_emits_fallback_instruction_not_buckets():
    significant = [
        _row("Salaries", 50_000, 55_000, 5_000, 10.0),
        _row("Professional Fees", 10_000, 15_000, 5_000, 50.0),
    ]
    insignificant: list[dict] = []
    text = build_user_message(significant, insignificant)
    assert "Full report totals" not in text
    assert "Revenue (reported lines) totals:" not in text
    assert "Expense (reported lines) totals:" not in text
    assert "Do not state a single consolidated" in text


def test_sales_and_marketing_programs_is_expense_bucket():
    significant = [
        _row("Revenue", 200_000, 190_000, -10_000, -5.0),
        _row("Sales & Marketing Programs", 40_000, 48_000, 8_000, 20.0),
    ]
    insignificant: list[dict] = []
    text = build_user_message(significant, insignificant)
    assert "Full report totals" not in text
    assert "Revenue (reported lines) totals:" in text
    assert "Expense (reported lines) totals:" in text
    assert "Sales & Marketing Programs" in text
