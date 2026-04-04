from __future__ import annotations

import re
from pathlib import Path

from docx import Document

_SECTION_TITLES = frozenset(
    {"EXECUTIVE SUMMARY", "LINE COMMENTARY", "INSIGNIFICANT VARIANCES"}
)


def _slug_period(period: str) -> str:
    raw = (period or "").strip()
    cleaned = re.sub(r"[^\w\s-]", "", raw, flags=re.UNICODE)
    slug = re.sub(r"\s+", "_", cleaned.strip())
    return slug or "unknown_period"


def build_export_basename(period: str, extension: str) -> str:
    ext = extension.lstrip(".").lower()
    return f"variance_commentary_{_slug_period(period)}.{ext}"


def write_markdown(commentary: str, dest_path: Path) -> None:
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_text(commentary, encoding="utf-8", newline="\n")


def write_docx(commentary: str, dest_path: Path) -> None:
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    document = Document()
    lines = commentary.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    buffer: list[str] = []

    def flush_paragraph() -> None:
        nonlocal buffer
        body = "\n".join(buffer).strip()
        buffer = []
        if body:
            document.add_paragraph(body)

    for line in lines:
        stripped = line.strip()
        if stripped in _SECTION_TITLES:
            flush_paragraph()
            document.add_heading(stripped, level=1)
        elif not stripped:
            flush_paragraph()
        else:
            buffer.append(line)
    flush_paragraph()
    document.save(str(dest_path))
