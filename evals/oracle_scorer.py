from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agent.models import AgentRun, Evidence, ParsedLineItem


_NO_EVIDENCE_SNIPPETS = (
    "no results returned",
    "no evidence found",
    "no context found",
    "n/a",
)

_SPECULATIVE_MARKERS = (
    "may reflect",
    "may indicate",
    "could reflect",
    "could indicate",
    "suggesting",
    "whether this reflects",
    "whether volume",
    "whether higher transaction volume",
    "whether incremental",
    "whether this is",
)

_ABSTENTION_MARKERS = (
    "no context found",
    "no supporting context",
    "no supporting evidence",
    "no evidence",
    "requires review",
    "recommend review",
    "direct review",
    "management review",
    "unsubstantiated",
    "evidence is absent",
)

_MIXED_TOTAL_PATTERNS = (
    "closed at $",
    "actuals of $",
    "total costs and revenue",
    "total actuals of $",
)


@dataclass
class OracleLineResult:
    line_item: str
    supported: bool
    numbers_match: bool
    evidence_match: bool
    driver_match: bool
    action_match: bool
    abstained_cleanly: bool
    invented_specifics: bool
    placeholder_sources: bool
    line_score: float
    max_score: float


def _normalize(text: str) -> str:
    return " ".join(str(text).lower().strip().split())


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _meaningful_source(source: Evidence) -> bool:
    source_id = _normalize(source.id)
    source_type = _normalize(source.source_type)
    timestamp = _normalize(source.timestamp)
    snippet = _normalize(source.snippet)
    if not source_id or source_id == "n/a":
        return False
    if not source_type or source_type == "malformed_source":
        return False
    if any(marker in timestamp for marker in _NO_EVIDENCE_SNIPPETS):
        return False
    if any(marker in snippet for marker in _NO_EVIDENCE_SNIPPETS):
        return False
    return True


def _has_placeholder_sources(item: ParsedLineItem) -> bool:
    return bool(item.sources) and not any(_meaningful_source(source) for source in item.sources)


def _line_index(agent_run: AgentRun) -> dict[str, ParsedLineItem]:
    return {_normalize(item.line_item_name): item for item in agent_run.line_items}


def _numbers_match(item: ParsedLineItem, oracle_line: dict[str, Any]) -> bool:
    expected = (
        float(oracle_line.get("budget_usd", 0.0)),
        float(oracle_line.get("actual_usd", 0.0)),
        float(oracle_line.get("variance_usd", 0.0)),
    )
    actual = (
        float(item.budget_usd or 0.0),
        float(item.actual_usd or 0.0),
        float(item.variance_usd or 0.0),
    )
    return all(abs(a - b) < 0.01 for a, b in zip(actual, expected))


def _matches_driver(text: str, oracle_line: dict[str, Any]) -> bool:
    expected_driver = _normalize(oracle_line.get("expected_driver", ""))
    keywords = [_normalize(keyword) for keyword in oracle_line.get("expected_driver_keywords", [])]
    normalized_text = _normalize(text)
    if expected_driver and expected_driver in normalized_text:
        return True
    if keywords:
        hits = sum(1 for keyword in keywords if keyword and keyword in normalized_text)
        return hits >= min(2, len(keywords))
    return False


def _matches_action(text: str, oracle_line: dict[str, Any]) -> bool:
    normalized_text = _normalize(text)
    action = _normalize(oracle_line.get("mitigation_or_action", ""))
    risk = _normalize(oracle_line.get("forward_risk", ""))
    action_keywords = [_normalize(word) for word in action.split() if len(word) > 4]
    risk_keywords = [_normalize(word) for word in risk.split() if len(word) > 4]
    if action and action in normalized_text:
        return True
    if risk and risk in normalized_text:
        return True
    return any(keyword in normalized_text for keyword in action_keywords + risk_keywords)


def _matches_expected_evidence(item: ParsedLineItem, oracle_line: dict[str, Any]) -> bool:
    expected_ids = {_normalize(value) for value in oracle_line.get("expected_evidence_ids", [])}
    allowed_families = {_normalize(value) for value in oracle_line.get("allowed_source_families", [])}
    meaningful_sources = [source for source in item.sources if _meaningful_source(source)]
    if expected_ids and any(_normalize(source.id) in expected_ids for source in meaningful_sources):
        return True
    if allowed_families and any(_normalize(source.source_type) in allowed_families for source in meaningful_sources):
        return True
    return False


def _abstained_cleanly(item: ParsedLineItem) -> bool:
    text = _normalize(item.final_commentary)
    if not any(marker in text for marker in _ABSTENTION_MARKERS):
        return False
    if _has_placeholder_sources(item):
        return False
    return not any(marker in text for marker in _SPECULATIVE_MARKERS)


def _invented_specifics(item: ParsedLineItem) -> bool:
    text = _normalize(item.final_commentary)
    return any(marker in text for marker in _SPECULATIVE_MARKERS)


def _score_line(item: ParsedLineItem | None, oracle_line: dict[str, Any]) -> OracleLineResult:
    supported = bool(oracle_line.get("supported"))
    if item is None:
        return OracleLineResult(
            line_item=str(oracle_line["line_item"]),
            supported=supported,
            numbers_match=False,
            evidence_match=False,
            driver_match=False,
            action_match=False,
            abstained_cleanly=False,
            invented_specifics=False,
            placeholder_sources=False,
            line_score=0.0,
            max_score=6.0,
        )

    numbers_match = _numbers_match(item, oracle_line)
    placeholder_sources = _has_placeholder_sources(item)
    evidence_match = _matches_expected_evidence(item, oracle_line) if supported else False
    driver_match = _matches_driver(item.final_commentary, oracle_line) if supported else False
    action_match = _matches_action(item.final_commentary, oracle_line) if supported else False
    abstained_cleanly = _abstained_cleanly(item) if not supported else False
    invented_specifics = _invented_specifics(item) if not supported else False

    score = 1.0 if numbers_match else 0.0
    if supported:
        if evidence_match:
            score += 2.0
        if driver_match:
            score += 2.0
        if action_match:
            score += 1.0
    else:
        if abstained_cleanly:
            score += 3.0
        if not invented_specifics:
            score += 1.0
        if not placeholder_sources:
            score += 1.0
        if not any(_meaningful_source(source) for source in item.sources):
            score += 1.0
    score = min(score, 6.0)

    return OracleLineResult(
        line_item=str(oracle_line["line_item"]),
        supported=supported,
        numbers_match=numbers_match,
        evidence_match=evidence_match,
        driver_match=driver_match,
        action_match=action_match,
        abstained_cleanly=abstained_cleanly,
        invented_specifics=invented_specifics,
        placeholder_sources=placeholder_sources,
        line_score=score,
        max_score=6.0,
    )


def _summary_sentence_parts(text: str) -> list[str]:
    return [
        part.strip()
        for part in re.split(
            r"(?<![0-9])(?<!vs)(?<!\))\.(?:\s+|$)",
            text.strip(),
        )
        if part.strip()
    ]


def _summary_usefulness(agent_run: AgentRun, oracle: dict[str, Any]) -> float:
    summary = _normalize(agent_run.executive_summary)
    expectations = oracle.get("summary_expectations", {})
    must_surface = [_normalize(value) for value in expectations.get("must_surface_lines", [])]
    surfaced = (
        sum(1 for value in must_surface if value in summary) / len(must_surface)
        if must_surface
        else 0.0
    )
    sentence_parts = _summary_sentence_parts(agent_run.executive_summary.strip())
    concise = 1.0 if 1 <= len(sentence_parts) <= 4 else 0.5
    mixed_total_ok = 1.0
    if expectations.get("forbid_mixed_total_story"):
        if any(pattern in summary for pattern in _MIXED_TOTAL_PATTERNS):
            mixed_total_ok = 0.0
    return round((surfaced + concise + mixed_total_ok) / 3.0, 4)


def _formatting_polish(agent_run: AgentRun, oracle: dict[str, Any]) -> float:
    expected_lines = sum(1 for line in oracle.get("lines", []) if line.get("significant", True))
    has_summary = 1.0 if agent_run.executive_summary.strip() else 0.0
    coverage = min(1.0, len(agent_run.line_items) / expected_lines) if expected_lines else 1.0
    has_insignificant = 1.0 if agent_run.insignificant else 0.5
    return round((has_summary + coverage + has_insignificant) / 3.0, 4)


def score_agent_run(agent_run: AgentRun, oracle: dict[str, Any]) -> dict[str, Any]:
    indexed_items = _line_index(agent_run)
    line_results = [
        _score_line(indexed_items.get(_normalize(str(line["line_item"]))), line)
        for line in oracle.get("lines", [])
        if line.get("significant", True)
    ]

    supported_results = [line for line in line_results if line.supported]
    unsupported_results = [line for line in line_results if not line.supported]

    supported_line_recall = (
        sum(1 for line in supported_results if line.evidence_match) / len(supported_results)
        if supported_results
        else 0.0
    )
    driver_accuracy = (
        sum(1 for line in supported_results if line.driver_match) / len(supported_results)
        if supported_results
        else 0.0
    )
    unsupported_line_precision = (
        sum(1 for line in unsupported_results if line.abstained_cleanly) / len(unsupported_results)
        if unsupported_results
        else 1.0
    )
    evidence_citation_quality = (
        sum(1 for line in supported_results if line.evidence_match and not line.placeholder_sources) / len(supported_results)
        if supported_results
        else 0.0
    )
    significant_line_truthfulness = (
        sum(line.line_score / line.max_score for line in supported_results) / len(supported_results)
        if supported_results
        else 0.0
    )

    summary_usefulness = _summary_usefulness(agent_run, oracle)
    formatting_polish = _formatting_polish(agent_run, oracle)

    breakdown = {
        "significant_line_truthfulness": round(significant_line_truthfulness * 45.0, 2),
        "abstention_honesty": round(unsupported_line_precision * 20.0, 2),
        "summary_usefulness": round(summary_usefulness * 20.0, 2),
        "evidence_citation_quality": round(evidence_citation_quality * 10.0, 2),
        "formatting_and_polish": round(formatting_polish * 5.0, 2),
    }
    score_100 = round(sum(breakdown.values()), 2)

    return {
        "workbook": oracle.get("workbook", ""),
        "run_id": agent_run.run_id,
        "score_100": score_100,
        "breakdown": breakdown,
        "metrics": {
            "supported_line_recall": round(supported_line_recall, 4),
            "unsupported_line_precision": round(unsupported_line_precision, 4),
            "driver_accuracy": round(driver_accuracy, 4),
            "summary_usefulness": round(summary_usefulness, 4),
            "evidence_citation_quality": round(evidence_citation_quality, 4),
            "formatting_and_polish": round(formatting_polish, 4),
        },
        "line_results": [
            {
                "line_item": line.line_item,
                "supported": line.supported,
                "numbers_match": line.numbers_match,
                "evidence_match": line.evidence_match,
                "driver_match": line.driver_match,
                "action_match": line.action_match,
                "abstained_cleanly": line.abstained_cleanly,
                "invented_specifics": line.invented_specifics,
                "placeholder_sources": line.placeholder_sources,
                "line_score": round(line.line_score, 2),
                "max_score": line.max_score,
            }
            for line in line_results
        ],
    }


def score_saved_run(oracle_path: Path) -> dict[str, Any]:
    oracle = _load_json(oracle_path)
    run_path = Path(oracle["saved_run"])
    agent_run = AgentRun.from_dict(_load_json(run_path))
    return score_agent_run(agent_run, oracle)


def _report_line(result: dict[str, Any]) -> str:
    breakdown = result["breakdown"]
    metrics = result["metrics"]
    return (
        f"## {result['workbook']}\n\n"
        f"- Score: `{result['score_100']}/100`\n"
        f"- Supported recall: `{metrics['supported_line_recall']:.2f}`\n"
        f"- Unsupported precision: `{metrics['unsupported_line_precision']:.2f}`\n"
        f"- Driver accuracy: `{metrics['driver_accuracy']:.2f}`\n"
        f"- Summary usefulness: `{metrics['summary_usefulness']:.2f}`\n"
        f"- Breakdown: truthfulness `{breakdown['significant_line_truthfulness']}`, "
        f"abstention `{breakdown['abstention_honesty']}`, summary `{breakdown['summary_usefulness']}`, "
        f"evidence `{breakdown['evidence_citation_quality']}`, polish `{breakdown['formatting_and_polish']}`\n"
    )


def render_markdown_report(
    results: list[dict[str, Any]], *, title: str = "Oracle Baseline Round 1"
) -> str:
    average = round(sum(result["score_100"] for result in results) / len(results), 2) if results else 0.0
    worst = sorted(results, key=lambda item: item["score_100"])[:3]
    body = "\n".join(_report_line(result) for result in results)
    worst_lines = "\n".join(
        f"- `{item['workbook']}`: `{item['score_100']}/100`" for item in worst
    )
    return (
        f"# {title}\n\n"
        f"- Seeded workbooks: `{len(results)}`\n"
        f"- Average score: `{average}/100`\n\n"
        "## Worst performers\n\n"
        f"{worst_lines}\n\n"
        "## Per-workbook breakdown\n\n"
        f"{body}"
    )


def score_oracle_dir(oracle_dir: Path) -> list[dict[str, Any]]:
    return [
        score_saved_run(path)
        for path in sorted(oracle_dir.glob("*.json"))
        if path.name != "manifest.json"
    ]


def score_oracle_run_pair(oracle_path: Path, run_path: Path) -> dict[str, Any]:
    oracle = _load_json(oracle_path)
    agent_run = AgentRun.from_dict(_load_json(run_path))
    return score_agent_run(agent_run, oracle)


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    oracle_dir = root / "oracles"
    results = score_oracle_dir(oracle_dir)
    print(render_markdown_report(results))
