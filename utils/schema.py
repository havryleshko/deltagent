from __future__ import annotations

import re
from typing import Any

CANONICAL_COLUMNS: tuple[str, ...] = (
    "period",
    "line_item",
    "budget_usd",
    "actual_usd",
    "variance_usd",
    "variance_pct",
)

_CANONICAL_SET = frozenset(CANONICAL_COLUMNS)

_FORMAT_MAPS: dict[str, dict[str, str]] = {
    "canonical": {c: c for c in CANONICAL_COLUMNS},
    "xero_csv": {
        "account": "line_item",
        "budget": "budget_usd",
        "actual": "actual_usd",
        "variance": "variance_usd",
        "variance %": "variance_pct",
    },
    "sage": {
        "nominal": "line_item",
        "budget": "budget_usd",
        "actual": "actual_usd",
        "variance": "variance_usd",
    },
    "netsuite": {
        "account name": "line_item",
        "period budget": "budget_usd",
        "period actual": "actual_usd",
    },
    "quickbooks": {
        "account": "line_item",
    },
}

_FORMAT_FINGERPRINTS: dict[str, frozenset[str]] = {
    "canonical": frozenset(CANONICAL_COLUMNS),
    "netsuite": frozenset({"account name", "period budget", "period actual"}),
    "sage": frozenset({"nominal", "budget", "actual", "variance"}),
    "xero_csv": frozenset({"account", "budget", "actual", "variance"}),
    "quickbooks": frozenset({"account"}),
}

XLSX_FORMATS = frozenset({"xero_xlsx"})


def detect_format(columns: list[str]) -> str:
    cols = {c.lower().strip() for c in columns}
    for fmt in ("canonical", "netsuite", "sage", "xero_csv"):
        if _FORMAT_FINGERPRINTS[fmt].issubset(cols):
            return fmt
    return "unknown"


def _parse_numeric(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None
    raw = value.strip()
    if not raw:
        return None
    cleaned = raw.replace(",", "").replace(" ", "")
    cleaned = re.sub(r"[^\d.\-()+]", "", cleaned)
    is_paren_neg = cleaned.startswith("(") and cleaned.endswith(")")
    cleaned = cleaned.strip("()")
    if not cleaned:
        return None
    try:
        n = float(cleaned)
        return -n if is_paren_neg else n
    except ValueError:
        return None


def normalise_rows(
    raw_rows: list[dict[str, Any]],
    format_name: str,
    period: str | None = None,
    column_map: dict[str, str] | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    mapping: dict[str, str] = dict(_FORMAT_MAPS.get(format_name, {}))
    if column_map:
        mapping.update({k.lower().strip(): v.lower().strip() for k, v in column_map.items()})

    canonical_rows: list[dict[str, Any]] = []
    warnings: list[str] = []

    for row_idx, raw in enumerate(raw_rows, start=2):
        row: dict[str, Any] = {}
        for src_key, value in raw.items():
            target = mapping.get(src_key.lower().strip())
            if target:
                row[target] = value

        if "period" not in row and period:
            row["period"] = period

        parse_error = False
        for col in ("budget_usd", "actual_usd", "variance_usd", "variance_pct"):
            if col not in row:
                continue
            val = row[col]
            if isinstance(val, (int, float)):
                row[col] = float(val)
            else:
                parsed = _parse_numeric(str(val) if val is not None else "")
                if parsed is None:
                    warnings.append(f"Row {row_idx}: invalid value for {col!r}: {val!r}")
                    parse_error = True
                    break
                row[col] = parsed

        if parse_error:
            continue

        if "variance_usd" not in row and "actual_usd" in row and "budget_usd" in row:
            row["variance_usd"] = row["actual_usd"] - row["budget_usd"]

        if "variance_pct" not in row and "variance_usd" in row and "budget_usd" in row:
            budget = row["budget_usd"]
            variance = row["variance_usd"]
            row["variance_pct"] = (variance / abs(budget) * 100) if budget != 0 else 0.0

        canonical_rows.append(row)

    all_keys: set[str] = set()
    for row in canonical_rows:
        all_keys.update(row.keys())
    for col in CANONICAL_COLUMNS:
        if col not in all_keys:
            warnings.append(f"Column not mapped: {col}")

    return canonical_rows, warnings
