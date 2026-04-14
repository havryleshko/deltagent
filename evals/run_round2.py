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
class Round2Entry:
    slug: str
    workbook_path: Path
    mock_context_path: Path
    oracle_path: Path
    run_path: Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _round2_dir() -> Path:
    return Path(__file__).resolve().parent / "round2"


def _load_manifest(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return list(payload.get("bundles", []))


def _run_single_bundle(bundle: dict[str, Any], round2_dir: Path) -> Round2Entry:
    slug = str(bundle["slug"])
    workbook_path = round2_dir / str(bundle["xlsx"])
    mock_context_path = round2_dir / str(bundle["mock_context"])
    oracle_path = round2_dir / str(bundle["oracle"])
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
    return Round2Entry(
        slug=slug,
        workbook_path=workbook_path,
        mock_context_path=mock_context_path,
        oracle_path=oracle_path,
        run_path=run_path,
    )


def _build_mapping(entries: list[Round2Entry]) -> list[dict[str, str]]:
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


def run_round2(*, report_stem: str) -> tuple[Path, Path]:
    round2_dir = _round2_dir()
    bundles = _load_manifest(round2_dir / "manifest.json")
    entries = [_run_single_bundle(bundle, round2_dir) for bundle in bundles]
    mapping = _build_mapping(entries)

    mapping_path = round2_dir / f"{report_stem}_mapping.json"
    mapping_path.write_text(json.dumps(mapping, indent=2) + "\n", encoding="utf-8")

    scored = [
        score_oracle_run_pair(Path(row["oracle_path"]), Path(row["run_path"]))
        for row in mapping
    ]
    report_title = (
        "Round 2 Raw Baseline" if "raw" in report_stem else "Round 2 Post-fix Baseline"
    )
    report_path = round2_dir / f"{report_stem}.md"
    report_path.write_text(
        render_markdown_report(scored, title=report_title) + "\n", encoding="utf-8"
    )
    return mapping_path, report_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run round2 bundles and score outputs.")
    parser.add_argument(
        "--phase",
        choices=["raw", "postfix"],
        default="raw",
        help="Report phase label for output files.",
    )
    args = parser.parse_args()
    stem = "round2_raw_baseline" if args.phase == "raw" else "round2_postfix_baseline"
    mapping_path, report_path = run_round2(report_stem=stem)
    print(f"Wrote mapping: {mapping_path}")
    print(f"Wrote report: {report_path}")


if __name__ == "__main__":
    main()
