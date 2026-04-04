from __future__ import annotations

from pathlib import Path

from docx import Document

from exports.exporter import build_export_basename, write_docx, write_markdown

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
