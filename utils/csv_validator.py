from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any


REQUIRED_COLUMNS = {
    "period",
    "line_item",
    "budget_usd",
    "actual_usd",
    "variance_usd",
    "variance_pct",
}


def _parse_number(value: str) -> float:
    raw = (value or "").strip()
    if not raw:
        raise ValueError("empty numeric value")
    cleaned = raw.replace(",", "").replace(" ", "")
    cleaned = re.sub(r"[^\d\.\-\(\)%]", "", cleaned)
    is_paren_negative = cleaned.startswith("(") and cleaned.endswith(")")
    cleaned = cleaned.strip("()").replace("%", "")
    if not cleaned:
        raise ValueError(f"invalid numeric value: {value}")
    number = float(cleaned)
    return -number if is_paren_negative else number


def validate_csv(
    csv_path: str | Path,
    significance_pct_threshold: float = 10.0,
    significance_abs_variance_threshold: float = 1000.0,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    path = Path(csv_path)
    if not path.exists():
        return [], [], [f"CSV not found: {path}"]

    significant_rows: list[dict[str, Any]] = []
    insignificant_rows: list[dict[str, Any]] = []
    errors: list[str] = []

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        available_columns = set(reader.fieldnames or [])
        missing_columns = sorted(REQUIRED_COLUMNS - available_columns)
        if missing_columns:
            return [], [], [f"Missing required columns: {', '.join(missing_columns)}"]

        for index, row in enumerate(reader, start=2):
            try:
                normalized = {
                    "period": (row.get("period") or "").strip(),
                    "line_item": (row.get("line_item") or "").strip(),
                    "budget_usd": _parse_number(row.get("budget_usd") or ""),
                    "actual_usd": _parse_number(row.get("actual_usd") or ""),
                    "variance_usd": _parse_number(row.get("variance_usd") or ""),
                    "variance_pct": _parse_number(row.get("variance_pct") or ""),
                }
            except ValueError as error:
                errors.append(f"Row {index}: {error}")
                continue

            is_significant = (
                abs(normalized["variance_pct"]) > significance_pct_threshold
                and abs(normalized["variance_usd"]) > significance_abs_variance_threshold
            )
            if is_significant:
                significant_rows.append(normalized)
            else:
                insignificant_rows.append(normalized)

    return significant_rows, insignificant_rows, errors
