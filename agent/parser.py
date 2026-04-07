from __future__ import annotations

from agent.models import Evidence, ParsedLineItem


_SECTIONS = (
    "EXECUTIVE SUMMARY",
    "LINE COMMENTARY",
    "INSIGNIFICANT VARIANCES",
)


def _split_sections(text: str) -> dict[str, list[str]]:
    sections = {name: [] for name in _SECTIONS}
    current: str | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped in sections:
            current = stripped
            continue
        if current is not None:
            sections[current].append(line)
    return sections


def _looks_like_header(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and "|" in stripped and not stripped.startswith("-")


def _parse_source_line(line: str, fallback_index: int) -> Evidence:
    stripped = line.strip().lstrip("-").strip()
    if not stripped:
        return Evidence(
            id=f"source-{fallback_index}",
            source_type="source",
            timestamp="",
            snippet="",
        )
    parts = [part.strip() for part in stripped.split(" - ") if part.strip()]
    source_type = parts[0] if parts else "source"
    timestamp = parts[1] if len(parts) > 1 else ""
    evidence_id = parts[2] if len(parts) > 2 else f"{source_type.lower().replace(' ', '_')}-{fallback_index}"
    remainder = parts[3:] if len(parts) > 3 else []
    snippet = remainder[-1] if remainder else stripped
    ref = " - ".join(remainder[:-1]) if len(remainder) > 1 else ""
    return Evidence(
        id=evidence_id,
        source_type=source_type,
        timestamp=timestamp,
        snippet=snippet,
        ref=ref,
    )


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
        if stripped.lower().startswith("sources"):
            mode = "sources"
            continue
        if _looks_like_header(raw_line):
            flush()
            current_header = stripped
            continue
        if current_header is None:
            continue
        if mode == "sources":
            source_index += 1
            sources.append(_parse_source_line(raw_line, source_index))
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
