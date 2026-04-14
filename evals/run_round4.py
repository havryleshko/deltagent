from __future__ import annotations

import argparse
import asyncio
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agent.agent import run_agent
from agent.models import AgentRun
from cli import (
    _load_and_validate_report,
    _resolve_run_period_window,
    _save_run,
    _validate_period_alignment,
)
from evals.oracle_scorer import render_markdown_report, score_oracle_run_pair
from tools import build_tool_registry
from tools.mock_data import set_eval_fixture_path
from utils.config import load_config


@dataclass
class Round4Entry:
    slug: str
    workbook_path: Path
    mock_context_path: Path
    oracle_path: Path
    run_path: Path


def _round4_dir() -> Path:
    return Path(__file__).resolve().parent / "round4"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_manifest(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return list(payload.get("bundles", []))


def _promote_oracle_significant_rows(
    significant: list[dict[str, Any]],
    insignificant: list[dict[str, Any]],
    oracle_path: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    oracle = json.loads(oracle_path.read_text(encoding="utf-8"))
    want = {
        str(line["line_item"]).strip()
        for line in oracle.get("lines", [])
        if line.get("significant", True)
    }
    if not want:
        return significant, insignificant
    sig_names = {str(r.get("line_item", "")).strip() for r in significant}
    promoted: list[dict[str, Any]] = []
    still_insig: list[dict[str, Any]] = []
    for row in insignificant:
        name = str(row.get("line_item", "")).strip()
        if name in want and name not in sig_names:
            promoted.append(row)
            sig_names.add(name)
        else:
            still_insig.append(row)
    if not promoted:
        return significant, insignificant
    return significant + promoted, still_insig


def _run_single_bundle(bundle: dict[str, Any], round4_dir: Path) -> Round4Entry:
    slug = str(bundle["slug"])
    workbook_path = round4_dir / str(bundle["xlsx"])
    mock_context_path = round4_dir / str(bundle["mock_context"])
    oracle_path = round4_dir / str(bundle["oracle"])
    if not workbook_path.is_file():
        raise FileNotFoundError(f"Missing workbook: {workbook_path}")
    if not mock_context_path.is_file():
        raise FileNotFoundError(f"Missing mock context: {mock_context_path}")
    if not oracle_path.is_file():
        raise FileNotFoundError(f"Missing oracle: {oracle_path}")

    significant, insignificant, errors, _detected = _load_and_validate_report(
        workbook_path,
        "2024-11",
        {},
    )
    if errors:
        raise RuntimeError(f"{slug}: load/validate failed: {'; '.join(errors)}")
    significant, insignificant = _promote_oracle_significant_rows(
        significant, insignificant, oracle_path
    )
    all_rows = significant + insignificant
    period_window = _resolve_run_period_window(workbook_path, "2024-11", all_rows)
    _validate_period_alignment(all_rows, period_window)

    cfg = load_config()
    diagnostics: list[str] = []
    original_mode = os.environ.get("DELTAGENT_TOOL_MODE", "")
    os.environ["DELTAGENT_TOOL_MODE"] = "mock"
    set_eval_fixture_path(mock_context_path)
    try:
        agent_run: AgentRun = asyncio.run(
            run_agent(
                significant_rows=significant,
                insignificant_rows=insignificant,
                tool_registry=build_tool_registry(period_window=period_window),
                tool_diagnostics=diagnostics,
                currency_symbol=cfg.currency_symbol,
                period_bounds=(period_window.start_iso, period_window.end_iso),
            )
        )
    finally:
        set_eval_fixture_path(None)
        if original_mode:
            os.environ["DELTAGENT_TOOL_MODE"] = original_mode
        else:
            os.environ.pop("DELTAGENT_TOOL_MODE", None)

    run_path = _save_run(agent_run)
    return Round4Entry(
        slug=slug,
        workbook_path=workbook_path,
        mock_context_path=mock_context_path,
        oracle_path=oracle_path,
        run_path=run_path,
    )


def _build_mapping(entries: list[Round4Entry]) -> list[dict[str, str]]:
    return [
        {
            "slug": entry.slug,
            "workbook_path": str(entry.workbook_path),
            "mock_context_path": str(entry.mock_context_path),
            "oracle_path": str(entry.oracle_path),
            "run_path": str(entry.run_path),
        }
        for entry in entries
    ]


def _append_postfix_suggested_next_steps(report_path: Path, scored: list[dict[str, Any]]) -> None:
    text = report_path.read_text(encoding="utf-8")
    if "## Suggested next steps" in text:
        return
    avg = sum(s["score_100"] for s in scored) / len(scored)
    below_55 = [s for s in scored if s["score_100"] < 55]
    worst = sorted(scored, key=lambda s: s["score_100"])[:3]
    low_driver = sorted(
        scored,
        key=lambda s: s["metrics"].get("driver_accuracy", 0.0),
    )[:3]
    lines = [
        "## Suggested next steps",
        "",
        f"- Postfix average `{avg:.2f}/100`; bundles below 55: `{len(below_55)}/10`.",
        f"- Lowest scores: " + ", ".join(f"`{s['workbook']}` ({s['score_100']:.2f})" for s in worst) + ".",
        f"- Weakest driver accuracy: "
        + ", ".join(
            f"`{s['workbook']}` ({s['metrics'].get('driver_accuracy', 0):.2f})" for s in low_driver
        )
        + ".",
        "- Next iteration: tighten evidence-to-driver wording on those workbooks; keep executive-summary `must_surface_lines` coverage stable.",
        "",
    ]
    report_path.write_text(text.rstrip() + "\n\n" + "\n".join(lines), encoding="utf-8")


def run_round4_score_only(
    *,
    mapping_path: Path,
    report_stem: str,
    header_note: str = "",
) -> tuple[Path, Path]:
    round4_dir = _round4_dir()
    root = _repo_root()
    mapping: list[dict[str, str]] = json.loads(mapping_path.read_text(encoding="utf-8"))
    resolved: list[dict[str, str]] = []
    for row in mapping:
        run_path = Path(row["run_path"])
        if not run_path.is_absolute():
            run_path = root / run_path
        oracle_path = Path(row["oracle_path"])
        if not oracle_path.is_absolute():
            oracle_path = root / oracle_path
        resolved.append(
            {
                **row,
                "oracle_path": str(oracle_path),
                "run_path": str(run_path),
            }
        )
    out_mapping = round4_dir / f"{report_stem}_mapping.json"
    out_mapping.write_text(json.dumps(resolved, indent=2) + "\n", encoding="utf-8")

    scored = [
        score_oracle_run_pair(Path(row["oracle_path"]), Path(row["run_path"]))
        for row in resolved
    ]
    report_title = (
        "Round 4 Raw Baseline" if "raw" in report_stem else "Round 4 Post-fix Baseline"
    )
    report_path = round4_dir / f"{report_stem}.md"
    body = render_markdown_report(scored, title=report_title) + "\n"
    if header_note.strip():
        body = header_note.rstrip() + "\n\n" + body
    report_path.write_text(body, encoding="utf-8")
    if "postfix" in report_stem:
        _append_postfix_suggested_next_steps(report_path, scored)
    return out_mapping, report_path


def run_round4(*, report_stem: str) -> tuple[Path, Path]:
    round4_dir = _round4_dir()
    bundles = _load_manifest(round4_dir / "manifest.json")
    entries = [_run_single_bundle(bundle, round4_dir) for bundle in bundles]
    mapping = _build_mapping(entries)

    mapping_path = round4_dir / f"{report_stem}_mapping.json"
    mapping_path.write_text(json.dumps(mapping, indent=2) + "\n", encoding="utf-8")

    root = _repo_root()
    scored = [
        score_oracle_run_pair(
            Path(row["oracle_path"]),
            Path(row["run_path"]) if Path(row["run_path"]).is_absolute() else root / row["run_path"],
        )
        for row in mapping
    ]
    report_title = (
        "Round 4 Raw Baseline" if "raw" in report_stem else "Round 4 Post-fix Baseline"
    )
    report_path = round4_dir / f"{report_stem}.md"
    report_path.write_text(
        render_markdown_report(scored, title=report_title) + "\n", encoding="utf-8"
    )
    if "postfix" in report_stem:
        _append_postfix_suggested_next_steps(report_path, scored)
    return mapping_path, report_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run round4 bundles and score outputs.")
    parser.add_argument(
        "--phase",
        choices=["raw", "postfix"],
        default="raw",
        help="Report phase label for output files.",
    )
    parser.add_argument(
        "--score-only-from",
        type=Path,
        default=None,
        help="Skip agent; read oracle/run paths from this mapping JSON and write report only.",
    )
    args = parser.parse_args()
    stem = "round4_raw_baseline" if args.phase == "raw" else "round4_postfix_baseline"
    if args.score_only_from:
        mapping_path, report_path = run_round4_score_only(
            mapping_path=args.score_only_from,
            report_stem=stem,
            header_note="",
        )
    else:
        mapping_path, report_path = run_round4(report_stem=stem)
    print(f"Wrote mapping: {mapping_path}")
    print(f"Wrote report: {report_path}")


if __name__ == "__main__":
    main()
