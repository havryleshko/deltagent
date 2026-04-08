from __future__ import annotations

import re

from agent.models import Evidence, ParsedLineItem


_SECTIONS = (
    "EXECUTIVE SUMMARY",
    "LINE COMMENTARY",
    "INSIGNIFICANT VARIANCES",
)

_HEADER_PREFIX_RE = re.compile(r"^[#*\s]*\d*[.):\s]*")


def _split_sections(text: str) -> dict[str, list[str]]:
    sections = {name: [] for name in _SECTIONS}
    current: str | None = None
    for line in text.splitlines():
        stripped = line.strip()
        clean_upper = stripped.lstrip("#").strip().upper()
        matched = False
        for section_name in _SECTIONS:
            if clean_upper == section_name or clean_upper.startswith(section_name):
                current = section_name
                matched = True
                break
        if not matched and current is not None:
            sections[current].append(line)
    return sections


def _clean_header(raw: str) -> str:
    cleaned = _HEADER_PREFIX_RE.sub("", raw.strip()).strip()
    return cleaned.rstrip("*").rstrip()


def _looks_like_header(line: str) -> bool:
    stripped = line.strip()
    if stripped.startswith("|") or stripped.startswith("-"):
        return False
    return bool(stripped) and "|" in stripped


def _parse_source_line(line: str, fallback_index: int) -> Evidence | None:
    stripped = line.strip().lstrip("-").strip()
    if not stripped:
        return None
    parts = [part.strip() for part in re.split(r"\s+-\s+", stripped, maxsplit=3)]
    if len(parts) < 4:
        return Evidence(
            id=f"source-{fallback_index}",
            source_type="malformed_source",
            timestamp="",
            snippet=stripped,
        )
    source_type, timestamp, evidence_id, snippet = parts
    return Evidence(
        id=evidence_id,
        source_type=source_type,
        timestamp=timestamp,
        snippet=snippet,
    )


def _is_meaningful_source(source: Evidence) -> bool:
    return bool(source.snippet.strip()) and source.source_type not in {
        "",
        "source",
        "malformed_source",
    }


def parse_agent_output(
    text: str,
) -> tuple[str, list[ParsedLineItem], list[str], list[str]]:
    sections = _split_sections(text)
    executive_summary = "\n".join(sections["EXECUTIVE SUMMARY"]).strip()
    line_items: list[ParsedLineItem] = []
    current_header: str | None = None
    commentary_lines: list[str] = []
    sources: list[Evidence] = []
    mode = "commentary"
    source_index = 0

    def flush() -> None:
        nonlocal current_header, commentary_lines, sources, mode
        if not current_header:
            return
        line_items.append(
            ParsedLineItem(
                header=current_header.strip(),
                commentary="\n".join(line for line in commentary_lines if line.strip()).strip(),
                sources=list(sources),
            )
        )
        current_header = None
        commentary_lines = []
        sources = []
        mode = "commentary"

    for raw_line in sections["LINE COMMENTARY"]:
        stripped = raw_line.strip()
        if not stripped or stripped == "---":
            continue
        if re.match(r"^[-*#\s]*sources[*#:\s]*$", stripped, re.IGNORECASE):
            mode = "sources"
            continue
        if _looks_like_header(raw_line):
            flush()
            current_header = _clean_header(stripped)
            continue
        if current_header is None:
            continue
        if mode == "sources":
            source_index += 1
            source = _parse_source_line(raw_line, source_index)
            if source is not None:
                sources.append(source)
        else:
            commentary_lines.append(raw_line)
    flush()

    insignificant = [
        line.strip()
        for line in sections["INSIGNIFICANT VARIANCES"]
        if line.strip() and line.strip() != "---"
    ]

    gaps: list[str] = []
    for item in line_items:
        body = item.final_commentary.lower()
        if "no context found" in body or "tool failed" in body:
            gaps.append(item.header)
    return executive_summary, line_items, insignificant, gaps


_NO_EVIDENCE_MARKERS = (
    "no context found",
    "no evidence",
    "tool failed",
    "inferred — no source",
    "inferred - no source",
)


def validate_parsed_output(line_items: list[ParsedLineItem]) -> list[str]:
    warnings: list[str] = []
    for item in line_items:
        meaningful_sources = [source for source in item.sources if _is_meaningful_source(source)]
        has_sources = bool(meaningful_sources)
        has_any_sources = bool(item.sources)
        body_lower = item.final_commentary.lower()
        has_no_evidence = any(marker in body_lower for marker in _NO_EVIDENCE_MARKERS)
        if has_any_sources and not has_sources:
            warnings.append(f"Malformed or placeholder sources: {item.header!r}")
        elif has_sources and has_no_evidence:
            warnings.append(f"Contradictory no-evidence marker: {item.header!r}")
        elif not has_sources and not has_no_evidence:
            warnings.append(
                f"Missing sources or no-evidence marker: {item.header!r}"
            )
    return warnings
