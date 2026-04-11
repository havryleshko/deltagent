from __future__ import annotations

import csv
import io
import re
from pathlib import Path
from typing import Any

from tools.period_parse import resolve_period
from utils.schema import detect_format, infer_column_map, normalise_rows, parse_numeric


def _parse_xero_period_label(text: str) -> str:
    m = re.search(r"\d+\s+(\w+\s+\d{4})", text.strip())
    return m.group(1) if m else text.strip()


_XERO_SUBTOTAL_EXACT: frozenset[str] = frozenset({"gross profit", "net profit"})


def _is_xero_subtotal(account: str) -> bool:
    a = account.lower().strip()
    return a.startswith("total") or a in _XERO_SUBTOTAL_EXACT


def _load_xero_xlsx(path: Path, period: str | None = None) -> tuple[list[dict[str, Any]], str, list[str]]:
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
    resolved_period = period or _infer_period_label([_parse_xero_period_label(period_raw), path.stem])

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

        actual_f = parse_numeric(str(actual) if actual is not None else "")
        budget_f = parse_numeric(str(budget) if budget is not None else "") if budget is not None else 0.0
        if actual_f is None or budget_f is None:
            errors.append(f"Row {row_idx}: non-numeric value for {account!r}")
            continue

        variance = actual_f - budget_f
        variance_pct = (variance / abs(budget_f) * 100) if budget_f != 0 else 0.0

        canonical_rows.append(
            {
                "period": resolved_period or "",
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
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        return [], "unknown", [f"Could not read {path.name}: {exc}"]

    if not text.strip():
        return [], "unknown", [f"{path.name}: file is empty"]

    all_rows = _parse_delimited_rows(text)
    header_row_idx = _detect_header_row(all_rows)
    if header_row_idx is None:
        return [], "unknown", [
            f"{path.name}: could not identify a header row. Re-run with a clean export or use --column-map."
        ]

    fieldnames, raw_rows = _rows_to_dicts(all_rows, header_row_idx)
    if not fieldnames:
        return [], "unknown", [f"{path.name}: no columns found"]

    inferred_period = period or _infer_period_label(
        [path.stem] + [" ".join(str(cell or "") for cell in row[:4]) for row in all_rows[:8]]
    )
    fmt = detect_format(fieldnames)
    canonical_rows, warnings = normalise_rows(
        raw_rows, fmt, period=inferred_period, column_map=column_map
    )
    return canonical_rows, fmt, warnings


def load_report(
    path: Path,
    column_map: dict[str, str] | None = None,
    period: str | None = None,
) -> tuple[list[dict[str, Any]], str, list[str]]:
    suffix = path.suffix.lower()
    if suffix in (".xlsx", ".xls"):
        return _load_xero_xlsx(path, period=period)
    return _load_csv(path, column_map, period)


def _parse_delimited_rows(text: str) -> list[list[str]]:
    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    return [list(row) for row in csv.reader(io.StringIO(text), dialect)]


def _detect_header_row(rows: list[list[str]]) -> int | None:
    best_idx: int | None = None
    best_score = -1

    for idx, row in enumerate(rows[:15]):
        score = _score_header_row(row)
        if score > best_score:
            best_idx = idx
            best_score = score

    if best_idx is None or best_score < 4:
        return None
    return best_idx


def _score_header_row(row: list[str]) -> int:
    cells = [str(cell or "").strip() for cell in row]
    non_empty = [cell for cell in cells if cell]
    if len(non_empty) < 2:
        return -1

    fmt = detect_format(non_empty)
    mapping, _ = infer_column_map(non_empty, fmt)
    targets = set(mapping.values())
    numeric_like = sum(1 for cell in non_empty if parse_numeric(cell) is not None)

    score = len(targets)
    if fmt != "unknown":
        score += 10
    if "line_item" in targets:
        score += 2
    if "budget_usd" in targets:
        score += 1
    if "actual_usd" in targets:
        score += 1
    if numeric_like > max(1, len(non_empty) // 2):
        score -= 3
    return score


def _rows_to_dicts(rows: list[list[str]], header_row_idx: int) -> tuple[list[str], list[dict[str, str]]]:
    headers = _make_unique_headers(rows[header_row_idx])
    raw_rows: list[dict[str, str]] = []

    for row in rows[header_row_idx + 1 :]:
        if not any(str(cell or "").strip() for cell in row):
            continue
        padded = list(row[: len(headers)]) + [""] * max(0, len(headers) - len(row))
        raw_rows.append({headers[idx]: padded[idx] for idx in range(len(headers))})

    return headers, raw_rows


def _make_unique_headers(row: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    result: list[str] = []

    for idx, cell in enumerate(row, start=1):
        header = str(cell or "").strip() or f"Column {idx}"
        count = seen.get(header, 0) + 1
        seen[header] = count
        result.append(header if count == 1 else f"{header} {count}")

    return result


def _infer_period_label(texts: list[str]) -> str | None:
    labels: set[str] = set()
    for text in texts:
        if not text:
            continue
        for candidate in _extract_period_candidates(text):
            window = resolve_period(candidate)
            if window is not None:
                labels.add(window.label)
    if len(labels) == 1:
        return next(iter(labels))
    return None


def _extract_period_candidates(text: str) -> set[str]:
    normalized = str(text or "").replace("_", " ").replace("-", " ")
    candidates = {str(text or "").strip()}
    candidates.update(re.findall(r"\b\d{4}-\d{2}\b", str(text or "")))
    candidates.update(
        re.findall(
            r"\b(?:jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|sept|september|oct|october|nov|november|dec|december)\s+\d{4}\b",
            normalized,
            flags=re.IGNORECASE,
        )
    )
    return {candidate.strip() for candidate in candidates if candidate and candidate.strip()}
