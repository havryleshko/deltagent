from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

EVAL_DIR = Path(__file__).parents[1] / "eval"


def test_discover_cases_finds_all_seven():
    from eval.runner import discover_cases

    cases = discover_cases(EVAL_DIR)
    assert len(cases) == 7
    names = [c.name for c in cases]
    assert "case_01_xero_march_2026" in names
    assert "case_07_synth_revenue_miss" in names


def test_all_cases_have_required_files():
    for case_dir in EVAL_DIR.iterdir():
        if not case_dir.is_dir() or not case_dir.name.startswith("case_"):
            continue
        assert (case_dir / "input.csv").is_file(), f"{case_dir.name} missing input.csv"
        assert (case_dir / "mock_context.json").is_file(), f"{case_dir.name} missing mock_context.json"
        assert (case_dir / "config.json").is_file(), f"{case_dir.name} missing config.json"
        assert (case_dir / "notes.md").is_file(), f"{case_dir.name} missing notes.md"
        assert (case_dir / "expected_commentary.md").is_file(), f"{case_dir.name} missing expected_commentary.md"


def test_all_config_files_valid():
    from eval.runner import discover_cases, load_case_config

    for case_dir in discover_cases(EVAL_DIR):
        cfg = load_case_config(case_dir)
        assert "period" in cfg, f"{case_dir.name} config missing 'period'"
        assert "significance_pct" in cfg, f"{case_dir.name} config missing 'significance_pct'"
        assert "significance_abs" in cfg, f"{case_dir.name} config missing 'significance_abs'"


def test_all_mock_context_files_parseable():
    for case_dir in EVAL_DIR.iterdir():
        if not case_dir.is_dir() or not case_dir.name.startswith("case_"):
            continue
        ctx = json.loads((case_dir / "mock_context.json").read_text(encoding="utf-8"))
        assert "period" in ctx, f"{case_dir.name} mock_context missing 'period'"
        assert "tool_responses" in ctx, f"{case_dir.name} mock_context missing 'tool_responses'"


def test_all_input_csvs_load_without_errors():
    from utils.report_loader import load_report

    for case_dir in EVAL_DIR.iterdir():
        if not case_dir.is_dir() or not case_dir.name.startswith("case_"):
            continue
        rows, fmt, errors = load_report(case_dir / "input.csv")
        assert errors == [], f"{case_dir.name}: {errors}"
        assert len(rows) > 0, f"{case_dir.name}: no rows loaded"


def test_all_input_csvs_have_canonical_columns():
    from utils.report_loader import load_report
    from utils.schema import CANONICAL_COLUMNS

    for case_dir in EVAL_DIR.iterdir():
        if not case_dir.is_dir() or not case_dir.name.startswith("case_"):
            continue
        rows, _, _ = load_report(case_dir / "input.csv")
        assert rows, f"{case_dir.name}: empty rows"
        for col in CANONICAL_COLUMNS:
            assert col in rows[0], f"{case_dir.name}: missing column {col!r}"


def test_each_case_has_at_least_one_significant_row():
    from eval.runner import discover_cases, load_case_config
    from utils.csv_validator import validate_rows
    from utils.report_loader import load_report

    for case_dir in discover_cases(EVAL_DIR):
        cfg = load_case_config(case_dir)
        rows, _, _ = load_report(case_dir / "input.csv")
        sig, insig, errors = validate_rows(
            rows,
            significance_pct_threshold=float(cfg.get("significance_pct", 10.0)),
            significance_abs_variance_threshold=float(cfg.get("significance_abs", 1000.0)),
        )
        assert errors == [], f"{case_dir.name}: {errors}"
        assert len(sig) >= 1, (
            f"{case_dir.name}: no significant rows (pct={cfg['significance_pct']}, "
            f"abs={cfg['significance_abs']})"
        )


def test_set_eval_fixture_path_overrides_default(tmp_path):
    from tools.mock_data import set_eval_fixture_path, load_context

    fake_ctx = {"period": "Test 2099", "tool_responses": {}}
    fixture = tmp_path / "ctx.json"
    fixture.write_text(json.dumps(fake_ctx), encoding="utf-8")

    set_eval_fixture_path(fixture)
    try:
        ctx = load_context()
        assert ctx["period"] == "Test 2099"
    finally:
        set_eval_fixture_path(None)


def test_set_eval_fixture_path_none_restores_default():
    from tools.mock_data import set_eval_fixture_path, load_context, FIXTURE_PATH

    set_eval_fixture_path(None)
    ctx = load_context()
    assert ctx["period"] == "November 2024"


@pytest.mark.asyncio
async def test_run_case_produces_output(tmp_path):
    from eval.runner import run_case

    case_dir = EVAL_DIR / "case_07_synth_revenue_miss"

    fake_text = (
        "EXECUTIVE SUMMARY\nOctober 2024 revenue missed plan by $82K.\n\n"
        "Revenue | Budget: $500,000 | Actual: $418,000 | Variance: -$82,000 (-16.4%)\n"
        "Three deals slipped.\n\nNo context found — recommend review\n\n"
        "INSIGNIFICANT VARIANCES\nSoftware Licenses: within normal range.\n"
    )

    fake_response = MagicMock()
    fake_response.stop_reason = "end_turn"
    fake_response.content = [MagicMock(type="text", text=fake_text)]

    fake_client = MagicMock()
    fake_client.messages = MagicMock()
    fake_client.messages.create = AsyncMock(return_value=fake_response)

    with patch("agent.agent.build_system_prompt", return_value="sys"), \
         patch("agent.agent.build_user_message", return_value="user"):
        result = await run_case.__wrapped__(case_dir) if hasattr(run_case, "__wrapped__") else \
            await _run_case_with_client(case_dir, fake_client)

    assert result is not None


async def _run_case_with_client(case_dir: Path, client):
    from eval.runner import load_case_config
    from agent.agent import run_agent
    from tools import build_tool_registry
    from tools.mock_data import set_eval_fixture_path
    from tools.period_parse import resolve_period
    from utils.csv_validator import validate_rows
    from utils.report_loader import load_report
    import json

    cfg = load_case_config(case_dir)
    rows, _, _ = load_report(case_dir / "input.csv")
    significant, insignificant, _ = validate_rows(
        rows,
        significance_pct_threshold=float(cfg.get("significance_pct", 10.0)),
        significance_abs_variance_threshold=float(cfg.get("significance_abs", 1000.0)),
    )
    period_window = resolve_period(cfg["period"])
    mock_context = case_dir / "mock_context.json"
    set_eval_fixture_path(mock_context)
    import os
    os.environ["DELTAGENT_TOOL_MODE"] = "mock"
    try:
        agent_run = await run_agent(
            significant_rows=significant,
            insignificant_rows=insignificant,
            tool_registry=build_tool_registry(period_window=period_window),
            currency_symbol=cfg.get("currency_symbol", "$"),
            period_bounds=(period_window.start_iso, period_window.end_iso),
            client=client,
        )
    finally:
        set_eval_fixture_path(None)
        os.environ.pop("DELTAGENT_TOOL_MODE", None)
    return {"case": case_dir.name, "status": "ok", "run_id": agent_run.run_id}
