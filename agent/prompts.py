from __future__ import annotations

from typing import Any


SYSTEM_PROMPT = """You are DeltAgent, a finance variance commentary writer.

Output must contain exactly these top-level sections:
EXECUTIVE SUMMARY
LINE COMMENTARY
INSIGNIFICANT VARIANCES

Rules:
- State variance amount and direction first, then reason.
- Never fabricate reasons.
- If no supporting context exists, write: No context found — recommend review.
- If reason is inferred, add: (inferred — no source found)
- Keep tone professional and concise for executive readers.
- Do not omit any significant line item.
"""


def build_system_prompt() -> str:
    return SYSTEM_PROMPT


def _format_money(value: float) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.0f}"


def build_user_message(
    significant_rows: list[dict[str, Any]], insignificant_rows: list[dict[str, Any]]
) -> str:
    period = significant_rows[0]["period"] if significant_rows else (
        insignificant_rows[0]["period"] if insignificant_rows else "Unknown Period"
    )
    lines: list[str] = []
    lines.append(f"Period: {period}")
    lines.append("")
    lines.append("Significant variances:")
    if not significant_rows:
        lines.append("- None")
    for row in significant_rows:
        lines.append(
            "- "
            f"{row['line_item']} | Budget: {_format_money(row['budget_usd'])} | "
            f"Actual: {_format_money(row['actual_usd'])} | "
            f"Variance: {_format_money(row['variance_usd'])} ({row['variance_pct']:+.1f}%)"
        )
    lines.append("")
    lines.append("Insignificant variances:")
    if not insignificant_rows:
        lines.append("- None")
    for row in insignificant_rows:
        lines.append(
            "- "
            f"{row['line_item']} | Variance: {_format_money(row['variance_usd'])} "
            f"({row['variance_pct']:+.1f}%)"
        )
    return "\n".join(lines)
