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
_NUMERIC_COLUMNS = ("budget_usd", "actual_usd", "variance_usd", "variance_pct")


def normalize_header(value: str) -> str:
    raw = str(value or "").strip().lower()
    raw = raw.replace("%", " pct ")
    raw = raw.replace("$", " usd ")
    raw = re.sub(r"[_/\-]+", " ", raw)
    raw = re.sub(r"[^a-z0-9 ]+", " ", raw)
    return re.sub(r"\s+", " ", raw).strip()

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

_HEADER_ALIASES: dict[str, frozenset[str]] = {
    "period": frozenset(
        {
            "period",
            "month",
            "month name",
            "reporting period",
            "reporting month",
            "accounting period",
        }
    ),
    "line_item": frozenset(
        {
            "line item",
            "line_item",
            "account",
            "account name",
            "account description",
            "description",
            "nominal",
            "gl account",
            "category",
            "name",
        }
    ),
    "budget_usd": frozenset(
        {
            "budget",
            "budget usd",
            "budget amount",
            "budget $",
            "period budget",
            "mtd budget",
            "plan",
            "planned",
        }
    ),
    "actual_usd": frozenset(
        {
            "actual",
            "actual usd",
            "actual amount",
            "actuals",
            "actual $",
            "period actual",
            "mtd actual",
            "spent",
            "spend",
        }
    ),
    "variance_usd": frozenset(
        {
            "variance",
            "variance usd",
            "variance amount",
            "variance $",
            "difference",
            "diff",
            "delta",
        }
    ),
    "variance_pct": frozenset(
        {
            "variance pct",
            "variance percent",
            "variance percentage",
            "variance %",
            "diff %",
            "delta %",
            "change %",
        }
    ),
}

_FORMAT_FINGERPRINTS: dict[str, frozenset[str]] = {
    "canonical": frozenset(normalize_header(column) for column in CANONICAL_COLUMNS),
    "netsuite": frozenset({"account name", "period budget", "period actual"}),
    "sage": frozenset({"nominal", "budget", "actual", "variance"}),
    "xero_csv": frozenset({"account", "budget", "actual", "variance"}),
    "quickbooks": frozenset({"account"}),
}

XLSX_FORMATS = frozenset({"xero_xlsx"})


def detect_format(columns: list[str]) -> str:
    cols = {normalize_header(c) for c in columns if normalize_header(c)}
    for fmt in ("canonical", "netsuite", "sage", "xero_csv"):
        if _FORMAT_FINGERPRINTS[fmt].issubset(cols):
            return fmt
    mapping, _ = infer_column_map(columns, "unknown")
    mapped_targets = set(mapping.values())
    if {"line_item", "budget_usd", "actual_usd"}.issubset(mapped_targets):
        return "mapped_csv"
    return "unknown"


def parse_numeric(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None
    raw = value.strip()
    if not raw:
        return None
    cleaned = raw.replace(",", "").replace(" ", "")
    cleaned = re.sub(r"[^\d.\-()+]", "", cleaned)
    if cleaned.endswith("-"):
        cleaned = f"-{cleaned[:-1]}"
    is_paren_neg = cleaned.startswith("(") and cleaned.endswith(")")
    cleaned = cleaned.strip("()")
    if not cleaned:
        return None
    try:
        number = float(cleaned)
        return -number if is_paren_neg else number
    except ValueError:
        return None


def infer_column_map(
    columns: list[str],
    format_name: str,
    column_map: dict[str, str] | None = None,
) -> tuple[dict[str, str], list[str]]:
    normalized_manual = {
        normalize_header(src): target.lower().strip()
        for src, target in (column_map or {}).items()
        if normalize_header(src)
    }
    normalized_base = {
        normalize_header(src): target
        for src, target in _FORMAT_MAPS.get(format_name, {}).items()
        if normalize_header(src)
    }

    mapping: dict[str, str] = {}
    warnings: list[str] = []
    used_targets: dict[str, str] = {}

    for column in columns:
        normalized = normalize_header(column)
        if not normalized:
            continue
        target = normalized_manual.get(normalized) or normalized_base.get(normalized) or _guess_target(normalized)
        if not target or target not in _CANONICAL_SET:
            continue
        existing = used_targets.get(target)
        if existing and existing != column:
            warnings.append(f"Multiple columns look like {target}: {existing!r}, {column!r}")
            continue
        mapping[column] = target
        used_targets[target] = column
    return mapping, warnings


def normalise_rows(
    raw_rows: list[dict[str, Any]],
    format_name: str,
    period: str | None = None,
    column_map: dict[str, str] | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    headers = list(raw_rows[0].keys()) if raw_rows else []
    mapping, mapping_warnings = infer_column_map(headers, format_name, column_map=column_map)

    canonical_rows: list[dict[str, Any]] = []
    warnings: list[str] = list(mapping_warnings)

    for row_idx, raw in enumerate(raw_rows, start=2):
        row: dict[str, Any] = {}
        for src_key, value in raw.items():
            target = mapping.get(src_key)
            if target:
                row[target] = value

        if "period" not in row and period:
            row["period"] = period

        line_item = str(row.get("line_item", "") or "").strip()
        if line_item and _looks_like_subtotal(line_item):
            continue
        if line_item:
            row["line_item"] = line_item

        parse_error = False
        for column in _NUMERIC_COLUMNS:
            if column not in row:
                continue
            parsed = parse_numeric(str(row[column]) if row[column] is not None else "")
            if parsed is None:
                warnings.append(f"Row {row_idx}: invalid value for {column!r}: {row[column]!r}")
                parse_error = True
                break
            row[column] = parsed

        if parse_error:
            continue

        if "variance_usd" not in row and "actual_usd" in row and "budget_usd" in row:
            row["variance_usd"] = row["actual_usd"] - row["budget_usd"]

        if "variance_pct" not in row and "variance_usd" in row and "budget_usd" in row:
            budget = row["budget_usd"]
            variance = row["variance_usd"]
            row["variance_pct"] = (variance / abs(budget) * 100) if budget != 0 else 0.0

        if "period" in row:
            row["period"] = str(row["period"]).strip()

        if row:
            canonical_rows.append(row)

    all_keys: set[str] = set()
    for row in canonical_rows:
        all_keys.update(row.keys())

    missing = [column for column in CANONICAL_COLUMNS if column not in all_keys]
    if missing:
        warnings.append(_missing_column_message(missing, headers))

    return canonical_rows, warnings


def _guess_target(normalized: str) -> str | None:
    for target, aliases in _HEADER_ALIASES.items():
        if normalized in aliases:
            return target

    tokens = set(normalized.split())
    if "variance" in tokens or "diff" in tokens or "delta" in tokens:
        if {"pct", "percent", "percentage"} & tokens:
            return "variance_pct"
        return "variance_usd"
    if "budget" in tokens or "plan" in tokens or "planned" in tokens:
        return "budget_usd"
    if "actual" in tokens or "actuals" in tokens or "spend" in tokens or "spent" in tokens:
        return "actual_usd"
    if "period" in tokens or "month" in tokens:
        return "period"
    if {"account", "nominal", "description", "category"} & tokens:
        return "line_item"
    return None


def _looks_like_subtotal(value: str) -> bool:
    normalized = normalize_header(value)
    return normalized.startswith("total ") or normalized in {
        "total",
        "subtotal",
        "gross profit",
        "net profit",
    }


def _missing_column_message(missing: list[str], headers: list[str]) -> str:
    available = ", ".join(repr(header) for header in headers[:8]) or "none"
    if missing == ["period"]:
        return "Could not determine period from the file. Re-run with --period YYYY-MM."
    return (
        f"Could not confidently map required columns: {', '.join(missing)}. "
        f"Available columns: {available}. Re-run with --column-map '<source>=<target>'."
    )
