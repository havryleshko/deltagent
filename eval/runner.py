from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

EVAL_DIR = Path(__file__).parent


def discover_cases(eval_dir: Path = EVAL_DIR) -> list[Path]:
    return sorted(
        p for p in eval_dir.iterdir()
        if p.is_dir() and p.name.startswith("case_")
    )


def load_case_config(case_dir: Path) -> dict[str, Any]:
    config_path = case_dir / "config.json"
    if not config_path.is_file():
        return {}
    with config_path.open(encoding="utf-8") as fh:
        return json.load(fh)


async def run_case(case_dir: Path, *, live: bool = False) -> dict[str, Any]:
    from agent.agent import run_agent
    from agent.models import AgentRun
    from tools import build_tool_registry
    from tools.mock_data import set_eval_fixture_path
    from tools.period_parse import resolve_period
    from utils.csv_validator import validate_rows
    from utils.report_loader import load_report

    cfg = load_case_config(case_dir)
    period_label = cfg.get("period", "")
    sig_pct = float(cfg.get("significance_pct", 10.0))
    sig_abs = float(cfg.get("significance_abs", 1000.0))
    currency = cfg.get("currency_symbol", "$")

    input_csv = case_dir / "input.csv"
    mock_context = case_dir / "mock_context.json"

    if not input_csv.is_file():
        return {"case": case_dir.name, "status": "error", "error": "missing input.csv"}
    if not mock_context.is_file() and not live:
        return {"case": case_dir.name, "status": "error", "error": "missing mock_context.json"}

    rows, _fmt, load_errors = load_report(input_csv)
    if load_errors:
        return {"case": case_dir.name, "status": "error", "error": "; ".join(load_errors)}

    significant, insignificant, validate_errors = validate_rows(
        rows,
        significance_pct_threshold=sig_pct,
        significance_abs_variance_threshold=sig_abs,
    )
    if validate_errors:
        return {"case": case_dir.name, "status": "error", "error": "; ".join(validate_errors)}

    period_window = resolve_period(period_label)
    if period_window is None:
        return {"case": case_dir.name, "status": "error", "error": f"Could not resolve period: {period_label!r}"}

    tool_mode = "live" if live else "mock"
    set_eval_fixture_path(mock_context if not live else None)

    import os
    original_mode = os.environ.get("DELTAGENT_TOOL_MODE", "")
    os.environ["DELTAGENT_TOOL_MODE"] = tool_mode

    try:
        tool_registry = build_tool_registry(period_window=period_window)
        agent_run: AgentRun = await run_agent(
            significant_rows=significant,
            insignificant_rows=insignificant,
            tool_registry=tool_registry,
            currency_symbol=currency,
            period_bounds=(period_window.start_iso, period_window.end_iso),
        )
    finally:
        if original_mode:
            os.environ["DELTAGENT_TOOL_MODE"] = original_mode
        else:
            os.environ.pop("DELTAGENT_TOOL_MODE", None)
        set_eval_fixture_path(None)

    outputs_dir = case_dir / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    output_path = outputs_dir / f"{agent_run.run_id}.json"
    output_path.write_text(
        json.dumps(agent_run.to_dict(), indent=2), encoding="utf-8"
    )

    return {
        "case": case_dir.name,
        "status": "ok",
        "run_id": agent_run.run_id,
        "significant": len(significant),
        "insignificant": len(insignificant),
        "gaps": agent_run.gaps,
        "output_path": str(output_path),
    }


async def run_all_async(
    filter_prefix: str | None = None,
    eval_dir: Path = EVAL_DIR,
    live: bool = False,
) -> list[dict[str, Any]]:
    cases = discover_cases(eval_dir)
    if filter_prefix:
        cases = [c for c in cases if filter_prefix in c.name]
    if not cases:
        print(f"No cases found matching {filter_prefix!r}")
        return []

    results = []
    for case_dir in cases:
        print(f"Running {case_dir.name} ...", flush=True)
        try:
            result = await run_case(case_dir, live=live)
        except Exception as exc:
            result = {"case": case_dir.name, "status": "error", "error": str(exc)}
        results.append(result)
        if result["status"] == "ok":
            n_gaps = len(result.get("gaps", []))
            print(
                f"  ✓  {result['significant']} significant, "
                f"{result['insignificant']} insignificant, "
                f"{n_gaps} gap(s) — run_id: {result['run_id']}"
            )
        else:
            print(f"  ✗  {result['error']}")
    return results


def run_all(
    filter_prefix: str | None = None,
    eval_dir: Path = EVAL_DIR,
    live: bool = False,
) -> list[dict[str, Any]]:
    return asyncio.run(run_all_async(filter_prefix=filter_prefix, eval_dir=eval_dir, live=live))


def _print_usage() -> None:
    print(
        "eval/runner.py [--list] [--live] [case_prefix]\n"
        "  --list   list cases\n"
        "  --live   live tool mode\n"
    )


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--list" in args:
        for case in discover_cases():
            cfg = load_case_config(case)
            print(f"{case.name}  ({cfg.get('period', '?')})")
        sys.exit(0)

    live = "--live" in args
    args = [a for a in args if a != "--live"]
    filter_prefix = args[0] if args else None

    results = run_all(filter_prefix=filter_prefix, live=live)
    failures = [r for r in results if r["status"] != "ok"]
    sys.exit(1 if failures else 0)
