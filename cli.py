from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Iterable, Optional

import typer
from dotenv import load_dotenv

from agent.agent import run_agent
from agent.models import AgentRun
from auth.google import google_auth_status, google_auth_test
from exports.exporter import export_from_run
from tools import build_tool_registry
from tools.period_parse import PeriodWindow, resolve_period
from ui.app import run_tui
from utils.config import load_config
from utils.csv_validator import validate_rows
from utils.report_loader import load_report

load_dotenv()

app = typer.Typer(help="DeltAgent CLI")
auth_app = typer.Typer(help="Authentication checks")
app.add_typer(auth_app, name="auth")


def _normalize_periods(rows: Iterable[dict[str, object]]) -> set[str]:
    labels: set[str] = set()
    for row in rows:
        raw = str(row.get("period", "") or "")
        window = resolve_period(raw)
        labels.add(window.label if window else raw.strip())
    return {item for item in labels if item}


def _run_dir() -> Path:
    path = Path("runs")
    path.mkdir(parents=True, exist_ok=True)
    return path


def _save_run(agent_run: AgentRun, path: Path | None = None) -> Path:
    dest = path or (_run_dir() / f"{agent_run.run_id}.json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(agent_run.to_dict(), indent=2), encoding="utf-8")
    return dest


def _load_run(path: Path) -> AgentRun:
    return AgentRun.from_dict(json.loads(path.read_text(encoding="utf-8")))


def _eligible_tools(line_item: str) -> list[str]:
    normalized = line_item.lower()
    tools = ["search_slack"]
    if "revenue" in normalized:
        tools.extend(["search_gmail", "search_calendar", "search_crm"])
    elif any(token in normalized for token in ("salary", "payroll", "headcount")):
        tools.extend(["search_gmail", "search_calendar"])
    else:
        tools.extend(["search_gmail", "search_calendar"])
    return tools


def _parse_column_map(items: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in items:
        if "=" in item:
            src, dst = item.split("=", 1)
            result[src.strip()] = dst.strip()
    return result


def _print_validation_summary(
    significant: list[dict[str, object]],
    insignificant: list[dict[str, object]],
    errors: list[str],
    detected_format: str | None = None,
) -> None:
    if detected_format:
        typer.echo(f"Detected format: {detected_format}")
    typer.echo(f"Significant rows: {len(significant)}")
    typer.echo(f"Insignificant rows: {len(insignificant)}")
    if errors:
        typer.echo("Validation errors:")
        for error in errors:
            typer.echo(f"- {error}")
    else:
        typer.echo("CSV validation passed.")


def _resolve_required_period(period: str) -> PeriodWindow:
    window = resolve_period(period)
    if window is None:
        raise typer.BadParameter("Period must be YYYY-MM or a month label like 'November 2024'.")
    return window


def _validate_period_alignment(
    rows: list[dict[str, object]], period_window: PeriodWindow
) -> None:
    labels = _normalize_periods(rows)
    if labels and labels != {period_window.label}:
        raise typer.BadParameter(
            f"CSV periods {sorted(labels)} do not match --period {period_window.label!r}."
        )


@app.command()
def tui(
    csv_path: Optional[str] = typer.Argument(default=None, help="Optional CSV path to open")
) -> None:
    run_tui(initial_csv_path=csv_path)


@app.command()
def validate(
    csv_path: Path = typer.Argument(..., exists=True, readable=True),
    period: Optional[str] = typer.Option(default=None, help="Optional explicit reporting period"),
    column_map: Optional[list[str]] = typer.Option(
        default=None, help="Column remapping, e.g. --column-map budget=budget_usd"
    ),
) -> None:
    cfg = load_config()
    col_map = _parse_column_map(column_map or [])
    rows, detected_format, load_errors = load_report(csv_path, column_map=col_map, period=period)
    significant, insignificant, validate_errors = validate_rows(
        rows,
        significance_pct_threshold=cfg.significance_pct_threshold,
        significance_abs_variance_threshold=cfg.significance_abs_variance_threshold,
    )
    errors = load_errors + validate_errors
    all_rows = significant + insignificant
    if period is not None and not errors:
        _validate_period_alignment(all_rows, _resolve_required_period(period))
    _print_validation_summary(significant, insignificant, errors, detected_format=detected_format)
    raise typer.Exit(code=1 if errors else 0)


@app.command()
def run(
    csv_path: Path = typer.Argument(..., exists=True, readable=True),
    period: str = typer.Option(..., help="Reporting period, e.g. 2025-11"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show the plan without executing"),
    column_map: Optional[list[str]] = typer.Option(
        default=None, help="Column remapping, e.g. --column-map budget=budget_usd"
    ),
) -> None:
    period_window = _resolve_required_period(period)
    cfg = load_config()
    col_map = _parse_column_map(column_map or [])
    rows, _detected_format, load_errors = load_report(
        csv_path, column_map=col_map, period=period_window.label
    )
    significant, insignificant, validate_errors = validate_rows(
        rows,
        significance_pct_threshold=cfg.significance_pct_threshold,
        significance_abs_variance_threshold=cfg.significance_abs_variance_threshold,
    )
    errors = load_errors + validate_errors
    all_rows = significant + insignificant
    _validate_period_alignment(all_rows, period_window)
    if errors:
        _print_validation_summary(significant, insignificant, errors, detected_format=_detected_format)
        raise typer.Exit(code=1)
    if dry_run:
        typer.echo(f"Period: {period_window.label}")
        typer.echo(f"Bounds: {period_window.start_iso} -> {period_window.end_iso}")
        typer.echo(f"Significant rows: {len(significant)}")
        typer.echo(f"Insignificant rows: {len(insignificant)}")
        typer.echo("")
        typer.echo("Planned tool calls:")
        if not significant:
            typer.echo("- No significant variances; run would generate summary-only output.")
        for row in significant:
            line_item = str(row["line_item"])
            typer.echo(f"- {line_item}: {', '.join(_eligible_tools(line_item))}")
        raise typer.Exit(code=0)
    if not os.environ.get("ANTHROPIC_API_KEY", "").strip():
        typer.echo("Missing ANTHROPIC_API_KEY.")
        raise typer.Exit(code=1)
    diagnostics: list[str] = []
    agent_run = asyncio.run(
        run_agent(
            significant_rows=significant,
            insignificant_rows=insignificant,
            tool_registry=build_tool_registry(period_window=period_window),
            tool_diagnostics=diagnostics,
            currency_symbol=cfg.currency_symbol,
            period_bounds=(period_window.start_iso, period_window.end_iso),
        )
    )
    run_path = _save_run(agent_run)
    typer.echo(agent_run.raw_text)
    if agent_run.gaps:
        typer.echo("")
        typer.echo("Visible gaps:")
        for gap in agent_run.gaps:
            typer.echo(f"- {gap}")
    if diagnostics:
        typer.echo("")
        typer.echo("Tool diagnostics:")
        for item in diagnostics:
            typer.echo(f"- {item}")
    typer.echo("")
    typer.echo(f"Saved run: {run_path}")


@auth_app.command("status")
def auth_status() -> None:
    ok, message = google_auth_status()
    typer.echo(message)
    raise typer.Exit(code=0 if ok else 1)


@auth_app.command("test")
def auth_test() -> None:
    ok, message = google_auth_test()
    typer.echo(message)
    raise typer.Exit(code=0 if ok else 1)


@auth_app.command("mcp-status")
def mcp_status() -> None:
    from mcp_client.config import load_mcp_servers, load_mcp_connection_state

    servers = load_mcp_servers()
    if not servers:
        typer.echo("No MCP servers configured (add [[mcp_servers]] to deltaagent.toml).")
        raise typer.Exit(code=0)
    any_connected = False
    for server in servers:
        state = load_mcp_connection_state(server)
        if state:
            tools = state.get("tools", [])
            typer.echo(f"{server.name}: connected — {len(tools)} tool(s): {', '.join(tools) or 'none'}")
            any_connected = True
        else:
            typer.echo(f"{server.name}: not connected (run: deltaagent auth mcp-connect --server {server.name})")
    raise typer.Exit(code=0 if any_connected else 1)


@auth_app.command("mcp-connect")
def mcp_connect(
    server_name: str = typer.Option(..., "--server", help="Name of the MCP server from deltaagent.toml"),
) -> None:
    from mcp_client.config import load_mcp_servers, save_mcp_connection_state
    from mcp_client import client as mcp_client

    servers = {s.name: s for s in load_mcp_servers()}
    if server_name not in servers:
        typer.echo(f"Server {server_name!r} not found in deltaagent.toml.")
        raise typer.Exit(code=1)
    server = servers[server_name]
    typer.echo(f"Connecting to {server.name} ({server.url}) …")
    try:
        tools = asyncio.run(mcp_client.discover_tools(server))
    except Exception as exc:
        typer.echo(f"Connection failed: {exc}")
        raise typer.Exit(code=1)
    tool_names = [t["name"] for t in tools]
    save_mcp_connection_state(server, tool_names)
    typer.echo(f"Connected. {len(tool_names)} tool(s) discovered: {', '.join(tool_names) or 'none'}")
    raise typer.Exit(code=0)


@app.command()
def review(run_path: Path = typer.Argument(..., exists=True, readable=True)) -> None:
    agent_run = _load_run(run_path)
    for item in agent_run.line_items:
        if item.review_status != "pending":
            continue
        typer.echo("")
        typer.echo(item.header)
        typer.echo(item.final_commentary)
        if item.sources:
            typer.echo("Sources:")
            for source in item.sources:
                typer.echo(
                    f"- {source.source_type} - {source.timestamp} - {source.id} - {source.snippet}"
                )
        action = typer.prompt("[A]ccept [E]dit [R]egenerate [F]lag [S]kip", default="s").strip().lower()
        if action == "a":
            item.review_status = "accepted"
        elif action == "e":
            item.edited_commentary = typer.prompt("Edited commentary")
            item.review_status = "edited"
        elif action == "f":
            item.flagged_reason = typer.prompt("Flag reason", default="")
            item.review_status = "flagged"
        elif action == "r":
            typer.echo("Regenerate is not implemented in Phase A; rerun `deltaagent run` if needed.")
        _save_run(agent_run, run_path)
    typer.echo(f"Review state saved: {run_path}")


@app.command()
def export(
    run_path: Path = typer.Argument(..., exists=True, readable=True),
    format: str = typer.Option("md", "--format", help="md or docx"),
    out_dir: Path = typer.Option(Path("."), "--out-dir", help="Destination directory"),
) -> None:
    agent_run = _load_run(run_path)
    dest = export_from_run(agent_run, format=format, out_dir=out_dir)
    typer.echo(f"Saved export: {dest}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
