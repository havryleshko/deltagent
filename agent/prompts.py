from __future__ import annotations

import re
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
- On supported lines, make the driver sentence trace to the tool excerpts: reuse at least two concrete terms or short phrases that appear in those excerpts (mechanisms, actors, timing) instead of vague paraphrase that drops them.
- Never fabricate reasons.
- If no supporting context exists, write: No context found — recommend review.
- If no supporting context exists, do not add hypothesized causes after that line; keep the commentary to the abstention only.
- If reason is inferred, add: (inferred — no source found)
- Keep tone professional and concise for executive readers.
- Do not omit any significant line item.
- Assess variance complexity first, then choose relevant tools.
- Use tools only for significant variance lines.
- Use broad queries first for each selected tool.
- If broad search is partial, conflicting, or does not reconcile the full variance, run one narrower follow-up query before writing that line.
- For one-off cost lines backed by invoices, approvals, emergency spend, repairs, or maintenance, run one narrow Gmail follow-up before finalizing the line if email may contain recovery, insurance, warranty, or secondary approval detail not visible in the broad result.
- Use search_calendar when timing or schedule context could explain the variance.
- Use search_crm for revenue and revenue-adjacent lines when deal, contract, onboarding, or project context could explain the variance, including Revenue, Professional Services, Cost of Revenue, and contractor/project-linked spend.
- Execute relevant tool calls in parallel each tool-use round.
- You may use multiple tool-use rounds until no additional tool calls are needed.
- Monetary amounts in the user message use the currency symbol shown there; mirror that symbol in your commentary.
- Every tool result is a JSON envelope with summary_for_model, evidence IDs, and timestamps.
- For each significant line item, render a Sources subsection immediately after the commentary.
- Each source line must be in the format: - SourceType - Timestamp - EvidenceID - Snippet
- If a source has placeholder values (for example EvidenceID `N/A` or text like `No evidence found`/`No results returned`), do not render that source line.
- If no meaningful sources remain for a line, omit the Sources subsection for that line.
- If a tool fails or returns no evidence, keep going and mention the visible gap in the commentary.
- Do not use markdown tables in your commentary. Use prose and bullet lists only.
- Do not claim a variance is fully explained unless the evidence actually reconciles the driver.
- If you cite aggregate totals in the executive summary, use Revenue or Expense bucket totals from the user message when present, or explicitly label significant-line totals; do not present a single consolidated actual vs budget for the full report unless the user message explicitly provides a labeled combined figure.
- Do not close the executive summary with combined rollup sentences such as "revenue actuals of $X beat budget" paired with "expense actuals of $Y" in the same paragraph; keep the opening summary anchored on named significant line items and their variance dollars.
- In the executive summary never write "actuals of", "total actuals", or "closed at $" (use "Revenue is $X vs budget $Y" or "LineName is over/under by $Z" instead).
- If evidence indicates timing, forecast, recovery, reserve, or remaining exposure but does not prove exact certainty, use cautious wording such as expected, likely, may, or requires confirmation.
- Avoid strong certainty phrases such as will, fully reconciled, fully explained, or no further spend is expected when the evidence is partial, estimated, or still pending confirmation.
- If a revenue miss mixes slipped deals and permanently lost deals, separate recoverable slippage from permanent loss instead of presenting the whole miss as a single recovery story.
- Do not instruct Finance to provision, reserve, or reforecast unless the evidence explicitly says that action has already been decided.
- Keep the board-pack register tight: lead with the driver, avoid operational play-by-play unless it changes the conclusion, and keep each line commentary to a few concise sentences before Sources.
- When evidence is partial, also avoid certain, guaranteed, no doubt, and will close / will complete / will settle unless the tool output explicitly confirms timing.
- Do not use second-person imperatives to Finance (for example "you should", "finance must") except optionally in a single closing Recommendation sentence framed as a suggestion.
- Keep each line item to at most three short bullets or two to four sentences before Sources; avoid "Key points:" or similar scaffolding.
- Write in a board-pack register: lead with the driver and variance, minimize operational play-by-play, and avoid markdown emphasis (**bold**) in body copy.
- If summary_for_model or evidence snippets contain a concrete fact (dates, amounts, insurance claim, venue credit, USPTO, credits), either reflect it in the line commentary or state explicitly that it is not yet reconciled to the ledger.
- Keep the executive summary to three short sentences max and each line commentary to two short sentences max unless bulleting is required to separate multiple distinct drivers.
- For downstream or derived lines such as Professional Services, Cost of Revenue, contractor/project-linked spend, or salary reclasses, if the first pass yields only one source family, run one corroborating follow-up from a second relevant source family before finalizing the line; if none exists, state that the evidence is single-source.
- When evidence is single-source or only partially corroborated, say that directly and avoid forecast advice, post-mortem suggestions, or operational next steps.
- Render the sources label exactly as Sources and each source row exactly as: - SourceType - Timestamp - EvidenceID - Snippet
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


_REVENUE_FORCE = frozenset({"subscription revenue"})
_EXPENSE_FORCE = frozenset({"sales & marketing programs", "marketing programs"})

_EXPENSE_TAG_TOKENS = (
    "salary",
    "salaries",
    "payroll",
    "fee",
    "fees",
    "rent",
    "marketing",
    "software",
    "subscription",
    "facility",
    "facilities",
    "travel",
    "fuel",
    "legal",
    "professional",
    "compliance",
    "audit",
    "hosting",
    "infrastructure",
    "contractor",
    "maintenance",
    "repair",
    "packaging",
    "freight",
    "merchant",
    "clinical",
    "cogs",
)


def _normalize_line_label(line_item: str) -> str:
    return line_item.lower().strip()


def _is_revenue_line_item(line_item: str) -> bool:
    n = _normalize_line_label(line_item)
    if not n:
        return False
    if n in _EXPENSE_FORCE:
        return False
    if n in _REVENUE_FORCE:
        return True
    if "cost of revenue" in n or "cost of sales" in n or re.search(r"\bcogs\b", n):
        return False
    if re.search(r"\bsales\b", n) and "marketing" in n:
        return False
    if re.search(r"\brevenue\b", n):
        return True
    if re.search(r"\bsales\b", n):
        return True
    return False


def _tag_expense_signal(line_item: str) -> bool:
    n = _normalize_line_label(line_item)
    if _is_revenue_line_item(line_item):
        return False
    return any(tok in n for tok in _EXPENSE_TAG_TOKENS)


def _tag_revenue_signal(line_item: str) -> bool:
    n = _normalize_line_label(line_item)
    if "cost of revenue" in n or "cost of sales" in n or re.search(r"\bcogs\b", n):
        return False
    if re.search(r"\bsales\b", n) and "marketing" in n:
        return False
    if re.search(r"\brevenue\b", n):
        return True
    if re.search(r"\bsales\b", n):
        return True
    return n in _REVENUE_FORCE


def _split_revenue_expense_rows(
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    revenue: list[dict[str, Any]] = []
    expense: list[dict[str, Any]] = []
    for row in rows:
        name = str(row.get("line_item", "") or "")
        if _is_revenue_line_item(name):
            revenue.append(row)
        else:
            expense.append(row)
    return revenue, expense


def _rollup_split_unreliable(all_rows: list[dict[str, Any]]) -> bool:
    revenue_rows, expense_rows = _split_revenue_expense_rows(all_rows)
    if not revenue_rows:
        return True
    names = [str(r.get("line_item", "") or "") for r in all_rows]
    tag_rev = any(_tag_revenue_signal(nm) for nm in names)
    tag_exp = any(_tag_expense_signal(nm) for nm in names)
    if tag_rev and tag_exp:
        if not expense_rows or not revenue_rows:
            return True
    return False


def _append_bucket_totals(
    lines: list[str],
    label: str,
    rows: list[dict[str, Any]],
    currency_symbol: str,
) -> None:
    if not rows:
        return
    b, a, v, vp = _rollup_rows(rows)
    lines.append(
        f"{label} "
        f"Budget: {_format_money(b, currency_symbol)} | "
        f"Actual: {_format_money(a, currency_symbol)} | "
        f"Variance: {_format_money(v, currency_symbol)} ({vp:+.1f}%)"
    )


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
        revenue_rows, expense_rows = _split_revenue_expense_rows(all_rows)
        if _rollup_split_unreliable(all_rows):
            lines.append(
                "Do not state a single consolidated actual vs budget for the full report; "
                "refer to significant lines and the bucket totals below only if present."
            )
        else:
            _append_bucket_totals(
                lines,
                "Revenue (reported lines) totals:",
                revenue_rows,
                currency_symbol,
            )
            _append_bucket_totals(
                lines,
                "Expense (reported lines) totals:",
                expense_rows,
                currency_symbol,
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
            "If you cite totals in the executive summary, prefer Revenue or Expense bucket totals when shown, "
            "or explicitly label significant-line totals."
        )
        lines.append(
            "Executive summary must explicitly name the top 3-5 material significant line items "
            "(using exact line-item labels) and tie each to its variance amount."
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
