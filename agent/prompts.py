from __future__ import annotations

from typing import Any


SYSTEM_PROMPT = """You are DeltAgent, a finance variance commentary writer.

Output must contain exactly these top-level sections:
EXECUTIVE SUMMARY
LINE COMMENTARY
INSIGNIFICANT VARIANCES

Header format for every line item in LINE COMMENTARY:
  <Line Item Name> | <Variance sign+amount> (<variance pct>) | Budget: <budget> | Actual: <actual>
  Example: Sales | +£5,003 (+83.4%) | Budget: £6,000 | Actual: £11,003
  IMPORTANT: The line item name MUST come first. Never start the header with "Variance:".

Rules:
- State variance amount and direction first, then reason.
- Never fabricate reasons.
- If no supporting context exists, write: No context found — recommend review.
- If reason is inferred, add: (inferred — no source found)
- Keep tone professional and concise for executive readers.
- Do not omit any significant line item.
- Assess variance complexity first, then choose relevant tools.
- Use tools only for significant variance lines.
- Use broad queries first for each selected tool.
- If broad search is partial, conflicting, or does not reconcile the full variance, run one narrower follow-up query before writing that line.
- Use search_calendar when timing or schedule context could explain the variance.
- Use search_crm for revenue and revenue-adjacent lines when deal, contract, onboarding, or project context could explain the variance, including Revenue, Professional Services, Cost of Revenue, and contractor/project-linked spend.
- Execute relevant tool calls in parallel each tool-use round.
- You may use multiple tool-use rounds until no additional tool calls are needed.
- Monetary amounts in the user message use the currency symbol shown there; mirror that symbol in your commentary.
- Every tool result is a JSON envelope with summary_for_model, evidence IDs, and timestamps.
- For each significant line item, render a Sources subsection immediately after the commentary.
- Each source line must be in the format: - SourceType - Timestamp - EvidenceID - Snippet
- If a tool fails or returns no evidence, keep going and mention the visible gap in the commentary.
- Do not use markdown tables in your commentary. Use prose and bullet lists only.
- Do not claim a variance is fully explained unless the evidence actually reconciles the driver.
- If you cite aggregate totals in the executive summary, either use the Full report totals from the user message exactly or explicitly label them as significant-line totals.
"""


def build_system_prompt() -> str:
    return SYSTEM_PROMPT


def _format_money(value: float, currency_symbol: str) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}{currency_symbol}{abs(value):,.0f}"


def _rollup_rows(rows: list[dict[str, Any]]) -> tuple[float, float, float, float]:
    budget = sum(float(row.get("budget_usd", 0) or 0) for row in rows)
    actual = sum(float(row.get("actual_usd", 0) or 0) for row in rows)
    variance = sum(float(row.get("variance_usd", 0) or 0) for row in rows)
    variance_pct = (variance / abs(budget) * 100) if budget else 0.0
    return budget, actual, variance, variance_pct


def build_user_message(
    significant_rows: list[dict[str, Any]],
    insignificant_rows: list[dict[str, Any]],
    currency_symbol: str = "$",
    period_start: str = "",
    period_end: str = "",
) -> str:
    all_rows = significant_rows + insignificant_rows
    period = significant_rows[0]["period"] if significant_rows else (
        insignificant_rows[0]["period"] if insignificant_rows else "Unknown Period"
    )
    lines: list[str] = []
    lines.append(f"Period: {period}")
    if period_start and period_end:
        lines.append(f"Hard date bounds: {period_start} to {period_end}")
    if all_rows:
        full_budget, full_actual, full_variance, full_variance_pct = _rollup_rows(all_rows)
        lines.append(
            "Full report totals: "
            f"Budget: {_format_money(full_budget, currency_symbol)} | "
            f"Actual: {_format_money(full_actual, currency_symbol)} | "
            f"Variance: {_format_money(full_variance, currency_symbol)} ({full_variance_pct:+.1f}%)"
        )
    if significant_rows:
        sig_budget, sig_actual, sig_variance, sig_variance_pct = _rollup_rows(significant_rows)
        lines.append(
            "Significant-line totals: "
            f"Budget: {_format_money(sig_budget, currency_symbol)} | "
            f"Actual: {_format_money(sig_actual, currency_symbol)} | "
            f"Variance: {_format_money(sig_variance, currency_symbol)} ({sig_variance_pct:+.1f}%)"
        )
        lines.append(
            "If you cite totals in the executive summary, use Full report totals unless you explicitly label them as significant-line totals."
        )
    lines.append("")
    lines.append("Significant variances:")
    if not significant_rows:
        lines.append("- None")
    for row in significant_rows:
        lines.append(
            "- "
            f"{row['line_item']} | Budget: {_format_money(row['budget_usd'], currency_symbol)} | "
            f"Actual: {_format_money(row['actual_usd'], currency_symbol)} | "
            f"Variance: {_format_money(row['variance_usd'], currency_symbol)} ({row['variance_pct']:+.1f}%)"
        )
    lines.append("")
    lines.append("Insignificant variances:")
    if not insignificant_rows:
        lines.append("- None")
    for row in insignificant_rows:
        lines.append(
            "- "
            f"{row['line_item']} | Variance: {_format_money(row['variance_usd'], currency_symbol)} "
            f"({row['variance_pct']:+.1f}%)"
        )
    return "\n".join(lines)
