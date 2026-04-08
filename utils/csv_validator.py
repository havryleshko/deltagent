from __future__ import annotations

from pathlib import Path
from typing import Any

from utils.schema import CANONICAL_COLUMNS
from utils.report_loader import load_report


def validate_rows(
    rows: list[dict[str, Any]],
    significance_pct_threshold: float = 10.0,
    significance_abs_variance_threshold: float = 1000.0,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    if not rows:
        return [], [], ["No data rows found"]

    missing = sorted(c for c in CANONICAL_COLUMNS if c not in rows[0])
    if missing:
        return [], [], [f"Missing required columns: {', '.join(missing)}"]

    significant: list[dict[str, Any]] = []
    insignificant: list[dict[str, Any]] = []

    for row in rows:
        try:
            is_significant = (
                abs(float(row.get("variance_pct", 0))) > significance_pct_threshold
                and abs(float(row.get("variance_usd", 0))) > significance_abs_variance_threshold
            )
        except (TypeError, ValueError):
            insignificant.append(row)
            continue
        if is_significant:
            significant.append(row)
        else:
            insignificant.append(row)

    return significant, insignificant, []


def validate_csv(
    csv_path: str | Path,
    significance_pct_threshold: float = 10.0,
    significance_abs_variance_threshold: float = 1000.0,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    path = Path(csv_path)
    if not path.exists():
        return [], [], [f"CSV not found: {path}"]

    rows, _fmt, load_errors = load_report(path)
    if load_errors:
        if not rows:
            return [], [], load_errors

    significant, insignificant, validate_errors = validate_rows(
        rows,
        significance_pct_threshold=significance_pct_threshold,
        significance_abs_variance_threshold=significance_abs_variance_threshold,
    )
    return significant, insignificant, load_errors + validate_errors
