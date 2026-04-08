from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

from utils.schema import CANONICAL_COLUMNS, detect_format, normalise_rows


def _parse_xero_period_label(text: str) -> str:
    m = re.search(r"\d+\s+(\w+\s+\d{4})", text.strip())
    return m.group(1) if m else text.strip()


_XERO_SUBTOTAL_EXACT: frozenset[str] = frozenset({"gross profit", "net profit"})


def _is_xero_subtotal(account: str) -> bool:
    a = account.lower().strip()
    return a.startswith("total") or a in _XERO_SUBTOTAL_EXACT


def _load_xero_xlsx(path: Path) -> tuple[list[dict[str, Any]], str, list[str]]:
    try:
        import openpyxl
    except ImportError:
        return [], "xero_xlsx", ["openpyxl is required for .xlsx files: pip install openpyxl"]

    try:
        wb = openpyxl.load_workbook(path, data_only=True)
    except Exception as exc:
        return [], "xero_xlsx", [f"Could not open {path.name}: {exc}"]

    ws = wb.active
    all_rows = list(ws.iter_rows(values_only=True))

    if len(all_rows) < 5:
        return [], "xero_xlsx", [f"{path.name}: unexpected xlsx structure (too few rows)"]

    period_raw = str(all_rows[2][0] or "")
    period = _parse_xero_period_label(period_raw)

    actual_col = 1
    budget_col = 2

    canonical_rows: list[dict[str, Any]] = []
    errors: list[str] = []

    for row_idx, row in enumerate(all_rows[5:], start=6):
        account = row[0]
        if account is None:
            continue
        account = str(account).strip()
        if not account:
            continue
        if _is_xero_subtotal(account):
            continue

        actual = row[actual_col] if len(row) > actual_col else None
        budget = row[budget_col] if len(row) > budget_col else None

        if actual is None:
            continue

        try:
            actual_f = float(actual)
            budget_f = float(budget) if budget is not None else 0.0
        except (TypeError, ValueError) as exc:
            errors.append(f"Row {row_idx}: non-numeric value for {account!r}: {exc}")
            continue

        variance = actual_f - budget_f
        variance_pct = (variance / abs(budget_f) * 100) if budget_f != 0 else 0.0

        canonical_rows.append(
            {
                "period": period,
                "line_item": account,
                "budget_usd": budget_f,
                "actual_usd": actual_f,
                "variance_usd": variance,
                "variance_pct": variance_pct,
            }
        )

    return canonical_rows, "xero_xlsx", errors


def _load_csv(
    path: Path,
    column_map: dict[str, str] | None,
    period: str | None,
) -> tuple[list[dict[str, Any]], str, list[str]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            raw_rows = list(reader)
            fieldnames: list[str] = list(reader.fieldnames or [])
    except OSError as exc:
        return [], "unknown", [f"Could not read {path.name}: {exc}"]

    if not fieldnames:
        return [], "unknown", [f"{path.name}: no columns found"]

    fmt = detect_format(fieldnames)
    canonical_rows, warnings = normalise_rows(
        raw_rows, fmt, period=period, column_map=column_map
    )
    return canonical_rows, fmt, warnings


def load_report(
    path: Path,
    column_map: dict[str, str] | None = None,
    period: str | None = None,
) -> tuple[list[dict[str, Any]], str, list[str]]:
    suffix = path.suffix.lower()
    if suffix in (".xlsx", ".xls"):
        return _load_xero_xlsx(path)
    return _load_csv(path, column_map, period)
