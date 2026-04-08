from __future__ import annotations

import csv
import tempfile
from pathlib import Path

import pytest

from utils.schema import CANONICAL_COLUMNS, detect_format, normalise_rows
from utils.report_loader import load_report
from utils.csv_validator import validate_rows, validate_csv


def test_detect_format_canonical():
    assert detect_format(list(CANONICAL_COLUMNS)) == "canonical"


def test_detect_format_xero_csv():
    assert detect_format(["Account", "Budget", "Actual", "Variance", "Variance %", "Period"]) == "xero_csv"


def test_detect_format_sage():
    assert detect_format(["Nominal", "Budget", "Actual", "Variance"]) == "sage"


def test_detect_format_netsuite():
    assert detect_format(["Account Name", "Period Budget", "Period Actual"]) == "netsuite"


def test_detect_format_unknown():
    assert detect_format(["foo", "bar", "baz"]) == "unknown"


def test_normalise_rows_canonical_parses_numeric():
    raw = [
        {
            "period": "November 2024",
            "line_item": "Revenue",
            "budget_usd": "100000",
            "actual_usd": "115000",
            "variance_usd": "15000",
            "variance_pct": "15",
        }
    ]
    rows, warnings = normalise_rows(raw, "canonical")
    assert warnings == []
    assert rows[0]["budget_usd"] == 100000.0
    assert rows[0]["actual_usd"] == 115000.0
    assert rows[0]["variance_pct"] == 15.0


def test_normalise_rows_xero_csv_remaps_columns():
    raw = [
        {
            "Account": "Sales",
            "Budget": "6000",
            "Actual": "7500",
            "Variance": "1500",
            "Variance %": "25",
        }
    ]
    rows, warnings = normalise_rows(raw, "xero_csv", period="March 2026")
    assert rows[0]["line_item"] == "Sales"
    assert rows[0]["budget_usd"] == 6000.0
    assert rows[0]["actual_usd"] == 7500.0
    assert rows[0]["period"] == "March 2026"


def test_normalise_rows_sage_remaps_columns():
    raw = [{"Nominal": "Salaries", "Budget": "50000", "Actual": "52000", "Variance": "2000"}]
    rows, warnings = normalise_rows(raw, "sage", period="January 2026")
    assert rows[0]["line_item"] == "Salaries"
    assert rows[0]["budget_usd"] == 50000.0
    assert rows[0]["variance_pct"] == pytest.approx(4.0)


def test_normalise_rows_netsuite_remaps_and_derives():
    raw = [{"Account Name": "Marketing", "Period Budget": "10000", "Period Actual": "12000"}]
    rows, warnings = normalise_rows(raw, "netsuite", period="February 2026")
    assert rows[0]["line_item"] == "Marketing"
    assert rows[0]["variance_usd"] == pytest.approx(2000.0)
    assert rows[0]["variance_pct"] == pytest.approx(20.0)


def test_normalise_rows_column_map_override():
    raw = [{"spend": "5000", "plan": "4000", "account_name": "Travel", "month": "October 2025"}]
    custom_map = {"spend": "actual_usd", "plan": "budget_usd", "account_name": "line_item", "month": "period"}
    rows, warnings = normalise_rows(raw, "unknown", column_map=custom_map)
    assert rows[0]["actual_usd"] == 5000.0
    assert rows[0]["line_item"] == "Travel"
    assert rows[0]["variance_usd"] == pytest.approx(1000.0)


def test_normalise_rows_gap_warning_for_missing_column():
    raw = [{"Account": "Sales", "Budget": "100", "Actual": "110"}]
    rows, warnings = normalise_rows(raw, "unknown")
    assert any("Column not mapped" in w for w in warnings)


def test_normalise_rows_skips_row_with_invalid_numeric():
    raw = [
        {"period": "Nov 2024", "line_item": "A", "budget_usd": "bad", "actual_usd": "100",
         "variance_usd": "10", "variance_pct": "10"},
        {"period": "Nov 2024", "line_item": "B", "budget_usd": "200", "actual_usd": "220",
         "variance_usd": "20", "variance_pct": "10"},
    ]
    rows, warnings = normalise_rows(raw, "canonical")
    assert len(rows) == 1
    assert rows[0]["line_item"] == "B"
    assert any("Row 2" in w for w in warnings)


def test_normalise_rows_derives_variance_when_absent():
    raw = [{"Account": "Fees", "Budget": "1000", "Actual": "1250"}]
    rows, _ = normalise_rows(raw, "xero_csv", period="March 2026")
    assert rows[0]["variance_usd"] == pytest.approx(250.0)
    assert rows[0]["variance_pct"] == pytest.approx(25.0)


def test_normalise_rows_zero_budget_variance_pct():
    raw = [{"Account": "Fees", "Budget": "0", "Actual": "500"}]
    rows, _ = normalise_rows(raw, "xero_csv", period="March 2026")
    assert rows[0]["variance_pct"] == 0.0


def test_load_report_canonical_csv(tmp_path: Path):
    f = tmp_path / "report.csv"
    f.write_text(
        "period,line_item,budget_usd,actual_usd,variance_usd,variance_pct\n"
        "November 2024,Revenue,100000,115000,15000,15\n"
        "November 2024,Salaries,50000,56000,6000,12\n",
        encoding="utf-8",
    )
    rows, fmt, errors = load_report(f)
    assert errors == []
    assert fmt == "canonical"
    assert len(rows) == 2
    assert rows[0]["line_item"] == "Revenue"
    assert rows[0]["budget_usd"] == 100000.0


def test_load_report_column_map_override(tmp_path: Path):
    f = tmp_path / "custom.csv"
    f.write_text(
        "period,account_name,spend,plan,diff,diff_pct\n"
        "March 2026,Sales,7500,6000,1500,25\n",
        encoding="utf-8",
    )
    col_map = {
        "account_name": "line_item",
        "spend": "actual_usd",
        "plan": "budget_usd",
        "diff": "variance_usd",
        "diff_pct": "variance_pct",
    }
    rows, fmt, errors = load_report(f, column_map=col_map)
    assert rows[0]["line_item"] == "Sales"
    assert rows[0]["actual_usd"] == 7500.0


def test_load_report_missing_file():
    rows, fmt, errors = load_report(Path("/nonexistent/file.csv"))
    assert errors
    assert rows == []


XERO_XLSX_FILES = [
    Path("/Users/ohavryleshko/Downloads/Demo_Company__UK__-_Budget_Variance.xlsx"),
    Path("/Users/ohavryleshko/Downloads/Demo_Company__UK__-_Budget_Variance-2.xlsx"),
    Path("/Users/ohavryleshko/Downloads/Demo_Company__UK__-_Budget_Variance-3.xlsx"),
]


@pytest.mark.parametrize("xlsx_path", XERO_XLSX_FILES)
def test_load_report_xero_xlsx(xlsx_path: Path):
    if not xlsx_path.exists():
        pytest.skip(f"Xero demo file not found: {xlsx_path}")
    rows, fmt, errors = load_report(xlsx_path)
    assert fmt == "xero_xlsx"
    assert errors == [], f"Unexpected errors: {errors}"
    assert len(rows) > 0
    for row in rows:
        for col in CANONICAL_COLUMNS:
            assert col in row, f"Missing column {col!r} in row {row}"
    assert all(row["period"] for row in rows)
    for row in rows:
        for col in ("budget_usd", "actual_usd", "variance_usd", "variance_pct"):
            assert isinstance(row[col], float), f"{col} is {type(row[col])}"


def test_load_report_xero_xlsx_period_label():
    xlsx = XERO_XLSX_FILES[0]
    if not xlsx.exists():
        pytest.skip("Xero demo file not found")
    rows, _, _ = load_report(xlsx)
    assert rows[0]["period"] == "March 2026"


def test_load_report_xero_xlsx_excludes_subtotals():
    xlsx = XERO_XLSX_FILES[0]
    if not xlsx.exists():
        pytest.skip("Xero demo file not found")
    rows, _, _ = load_report(xlsx)
    line_items = [r["line_item"] for r in rows]
    assert not any(li.lower().startswith("total") for li in line_items)
    assert "Gross Profit" not in line_items
    assert "Net Profit" not in line_items


def test_load_report_xero_xlsx_variance_computed():
    xlsx = XERO_XLSX_FILES[0]
    if not xlsx.exists():
        pytest.skip("Xero demo file not found")
    rows, _, _ = load_report(xlsx)
    for row in rows:
        expected = row["actual_usd"] - row["budget_usd"]
        assert abs(row["variance_usd"] - expected) < 0.01, (
            f"{row['line_item']}: variance_usd {row['variance_usd']:.2f} != {expected:.2f}"
        )


def test_validate_rows_splits_significance():
    rows = [
        {"period": "Nov 2024", "line_item": "Revenue", "budget_usd": 100000.0,
         "actual_usd": 115000.0, "variance_usd": 15000.0, "variance_pct": 15.0},
        {"period": "Nov 2024", "line_item": "Coffee", "budget_usd": 500.0,
         "actual_usd": 510.0, "variance_usd": 10.0, "variance_pct": 2.0},
    ]
    sig, insig, errors = validate_rows(rows)
    assert errors == []
    assert len(sig) == 1
    assert sig[0]["line_item"] == "Revenue"
    assert insig[0]["line_item"] == "Coffee"


def test_validate_rows_empty_returns_error():
    sig, insig, errors = validate_rows([])
    assert errors
    assert sig == []
    assert insig == []


def test_validate_rows_missing_column_returns_error():
    rows = [{"period": "Nov 2024", "line_item": "Revenue"}]
    sig, insig, errors = validate_rows(rows)
    assert any("Missing required columns" in e for e in errors)


def test_validate_csv_canonical_fixture():
    fixture = Path(__file__).parent / "fixtures" / "sample_november_2024.csv"
    from utils.csv_validator import validate_csv
    sig, insig, errors = validate_csv(fixture)
    assert errors == []
    assert {r["line_item"] for r in sig} == {"Revenue", "Salaries", "Professional Fees"}
    assert {r["line_item"] for r in insig} == {"Software & Subscriptions", "Office & Facilities"}


def test_validate_csv_bad_columns(tmp_path: Path):
    f = tmp_path / "bad.csv"
    f.write_text("not,valid,headers\n1,2,3\n", encoding="utf-8")
    from utils.csv_validator import validate_csv
    sig, insig, errors = validate_csv(f)
    assert errors
    assert sig == []
