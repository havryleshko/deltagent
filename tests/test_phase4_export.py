from __future__ import annotations

from pathlib import Path

from docx import Document

from agent.models import AgentRun, Evidence, ParsedLineItem
from exports.exporter import (
    build_export_basename,
    export_from_run,
    write_docx,
    write_markdown,
)

FIXTURE_COMMENTARY = """EXECUTIVE SUMMARY
One line summary.

LINE COMMENTARY

Revenue | Budget: $100 | Actual: $115
Overperformance explained here.

---

INSIGNIFICANT VARIANCES
Software: small.
"""


def test_build_export_basename_november():
    assert build_export_basename("November 2024", "md") == "variance_commentary_November_2024.md"
    assert build_export_basename("November 2024", "docx") == "variance_commentary_November_2024.docx"


def test_build_export_basename_sanitizes_period():
    name = build_export_basename("Q1 / 2024!", "md")
    assert name == "variance_commentary_Q1_2024.md"


def test_write_markdown_round_trip(tmp_path: Path) -> None:
    dest = tmp_path / "custom.md"
    write_markdown(FIXTURE_COMMENTARY, dest)
    assert dest.is_file()
    assert dest.read_text(encoding="utf-8") == FIXTURE_COMMENTARY


def test_write_docx_contains_section_headings(tmp_path: Path) -> None:
    dest = tmp_path / "out.docx"
    write_docx(FIXTURE_COMMENTARY, dest)
    assert dest.is_file()
    doc = Document(str(dest))
    texts = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    assert "EXECUTIVE SUMMARY" in texts
    assert "LINE COMMENTARY" in texts
    assert "INSIGNIFICANT VARIANCES" in texts
    assert any("Overperformance" in t for t in texts)


def test_export_from_run_uses_reviewed_lines_only(tmp_path: Path) -> None:
    agent_run = AgentRun(
        run_id="run_20240101_000000",
        period_label="November 2024",
        period_start="2024-11-01T00:00:00Z",
        period_end="2024-11-30T23:59:59Z",
        currency_symbol="$",
        raw_text=FIXTURE_COMMENTARY,
        executive_summary="One line summary.",
        line_items=[
            ParsedLineItem(
                header="Revenue | Budget: $100 | Actual: $115",
                commentary="Original commentary.",
                review_status="edited",
                edited_commentary="Edited commentary.",
                sources=[
                    Evidence(
                        id="gmail-1",
                        source_type="gmail",
                        timestamp="2024-11-10T10:00:00Z",
                        snippet="Approval thread",
                    )
                ],
            ),
            ParsedLineItem(
                header="Professional Fees | Budget: $10 | Actual: $16",
                commentary="Flagged item.",
                review_status="flagged",
            ),
        ],
        insignificant=["Software: small."],
    )
    dest = export_from_run(agent_run, "md", tmp_path)
    text = dest.read_text(encoding="utf-8")
    assert "Edited commentary." in text
    assert "Flagged item." not in text
    assert "gmail-1" in text
