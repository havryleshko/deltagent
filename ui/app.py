from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Checkbox, DataTable, Footer, Header, Input, RichLog, Static

from agent.agent import run_agent
from agent.models import AgentRun
from exports.exporter import export_from_run
from tools import build_tool_registry
from tools.period_parse import resolve_period
from utils.config import load_config
from utils.csv_validator import validate_rows
from utils.report_loader import load_report


def _save_tui_run(agent_run: AgentRun) -> Path:
    run_dir = Path("runs")
    run_dir.mkdir(parents=True, exist_ok=True)
    dest = run_dir / f"{agent_run.run_id}.json"
    dest.write_text(json.dumps(agent_run.to_dict(), indent=2), encoding="utf-8")
    return dest


class FilePickerScreen(Screen[str | None]):
    BINDINGS = [Binding("escape", "quit_app", "Quit")]

    def action_quit_app(self) -> None:
        self.app.exit()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Static("CSV path"),
            Input(placeholder="/path/to/file.csv", id="path_input"),
            Horizontal(
                Button("Open", variant="primary", id="open"),
                Button("Quit", id="quit"),
            ),
            id="picker_body",
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.app.exit()
            return
        if event.button.id != "open":
            return
        raw = self.query_one("#path_input", Input).value.strip()
        path = Path(raw).expanduser()
        if not path.is_file():
            self.app.notify("File not found", severity="error")
            return
        self.dismiss(str(path.resolve()))


class VarianceScreen(Screen[None]):
    def __init__(self, csv_path: str) -> None:
        super().__init__()
        self._csv_path = csv_path
        self._significant: list[dict[str, Any]] = []
        self._insignificant: list[dict[str, Any]] = []
        self._errors: list[str] = []
        self._currency_symbol = "$"

    def _fmt_money(self, value: float) -> str:
        sign = "-" if value < 0 else ""
        return f"{sign}{self._currency_symbol}{abs(value):,.0f}"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Static("", id="path_label"),
            Static("", id="period_label"),
            Static("", id="period_warning"),
            Static("", id="validation_errors"),
            DataTable(id="variance_table"),
            Checkbox("Confirm period", id="confirm"),
            Horizontal(
                Button("Run", variant="primary", id="run", disabled=True),
                Button("Back", id="back"),
            ),
            id="variance_body",
        )
        yield Footer()

    def on_mount(self) -> None:
        cfg = load_config()
        self._currency_symbol = cfg.currency_symbol
        self.query_one("#path_label", Static).update(f"File: {self._csv_path}")
        rows, _fmt, load_errors = load_report(self._csv_path)
        self._significant, self._insignificant, validate_errors = validate_rows(
            rows,
            significance_pct_threshold=cfg.significance_pct_threshold,
            significance_abs_variance_threshold=cfg.significance_abs_variance_threshold,
        )
        self._errors = load_errors + validate_errors
        err_widget = self.query_one("#validation_errors", Static)
        if self._errors:
            lines = list(self._errors)
            if any(
                line.startswith("Missing required columns") for line in self._errors
            ):
                lines = ["Fix the CSV and reload.", *lines]
            err_widget.update("\n".join(lines))
        else:
            err_widget.update("")
        all_rows = self._significant + self._insignificant
        if not all_rows:
            self.query_one("#period_label", Static).update("Period: —")
            self.query_one("#period_warning", Static).update("No rows loaded.")
            return
        periods = {r["period"] for r in all_rows if r.get("period")}
        first = self._significant[0] if self._significant else self._insignificant[0]
        period_text = first.get("period", "—")
        self.query_one("#period_label", Static).update(f"Period: {period_text}")
        warn_parts: list[str] = []
        if len(periods) > 1:
            warn_parts.append("Multiple periods in file — label uses first row's period.")
        if self._insignificant and not self._significant:
            warn_parts.append(
                "No line items exceed significance thresholds — commentary will emphasize "
                "executive summary and insignificant lines only."
            )
        self.query_one("#period_warning", Static).update("\n".join(warn_parts))
        table = self.query_one("#variance_table", DataTable)
        table.clear(columns=True)
        table.add_columns(
            "Line item",
            "Budget",
            "Actual",
            "Variance",
            "%",
            "Significant",
        )
        for row in self._significant:
            table.add_row(
                row["line_item"],
                self._fmt_money(row["budget_usd"]),
                self._fmt_money(row["actual_usd"]),
                self._fmt_money(row["variance_usd"]),
                f"{row['variance_pct']:+.1f}%",
                "Y",
            )
        for row in self._insignificant:
            table.add_row(
                row["line_item"],
                self._fmt_money(row["budget_usd"]),
                self._fmt_money(row["actual_usd"]),
                self._fmt_money(row["variance_usd"]),
                f"{row['variance_pct']:+.1f}%",
                "N",
            )
        self._update_run_enabled()

    def _update_run_enabled(self) -> None:
        run_btn = self.query_one("#run", Button)
        confirmed = self.query_one("#confirm", Checkbox).value
        has_rows = bool(self._significant or self._insignificant)
        run_btn.disabled = not confirmed or not has_rows

    @on(Checkbox.Changed, "#confirm")
    def on_confirm_changed(self, _event: Checkbox.Changed) -> None:
        self._update_run_enabled()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
            self.app.push_screen(FilePickerScreen(), callback=self.app._on_csv_chosen)
            return
        if event.button.id == "run":
            first = self._significant[0] if self._significant else self._insignificant[0]
            period = first.get("period", "Unknown")
            self.app.push_screen(
                CommentaryScreen(
                    significant_rows=list(self._significant),
                    insignificant_rows=list(self._insignificant),
                    period=period,
                    currency_symbol=self._currency_symbol,
                )
            )


class CommentaryScreen(Screen[None]):
    def __init__(
        self,
        significant_rows: list[dict[str, Any]],
        insignificant_rows: list[dict[str, Any]],
        period: str,
        currency_symbol: str,
    ) -> None:
        super().__init__()
        self._significant_rows = significant_rows
        self._insignificant_rows = insignificant_rows
        self._period = period
        self._currency_symbol = currency_symbol
        self._agent_run: AgentRun | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Static("", id="run_status"),
            RichLog(id="commentary_log", wrap=True, highlight=False, markup=False),
            Static("", id="tool_notes_title"),
            Static("", id="tool_notes"),
            Static("Export directory"),
            Input(value=".", id="export_dir"),
            Horizontal(
                Button("Export Markdown", id="export_md", disabled=True),
                Button("Export Word (.docx)", id="export_docx", disabled=True),
            ),
            Horizontal(
                Button("Run", variant="primary", id="run"),
                Button("Back", id="back"),
            ),
            id="commentary_body",
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
            return
        if event.button.id == "run":
            self.run_commentary()
            return
        if event.button.id == "export_md":
            self._export_commentary("md")
            return
        if event.button.id == "export_docx":
            self._export_commentary("docx")
            return

    @work(exclusive=True)
    async def run_commentary(self) -> None:
        status = self.query_one("#run_status", Static)
        log = self.query_one("#commentary_log", RichLog)
        notes_title = self.query_one("#tool_notes_title", Static)
        notes_body = self.query_one("#tool_notes", Static)
        run_btn = self.query_one("#run", Button)
        run_btn.disabled = True
        status.update("Generating commentary…")
        log.clear()
        notes_title.update("")
        notes_body.update("")
        diagnostics: list[str] = []
        agent_run: AgentRun | None = None
        error_message: str | None = None
        start = time.perf_counter()
        try:
            period_window = resolve_period(self._period)
            agent_run = await run_agent(
                significant_rows=self._significant_rows,
                insignificant_rows=self._insignificant_rows,
                tool_registry=build_tool_registry(period_window=period_window),
                tool_diagnostics=diagnostics,
                currency_symbol=self._currency_symbol,
                period_bounds=(
                    (period_window.start_iso, period_window.end_iso)
                    if period_window is not None
                    else None
                ),
            )
        except Exception as error:
            error_message = f"Run failed: {error}"
        finally:
            run_btn.disabled = False
        elapsed = time.perf_counter() - start
        suffix = f" ({elapsed:.1f}s)"
        if error_message is not None:
            status.update(f"Finished with error.{suffix}")
            log.write(error_message)
            self.query_one("#export_md", Button).disabled = True
            self.query_one("#export_docx", Button).disabled = True
            return
        assert agent_run is not None
        self._agent_run = agent_run
        try:
            run_path = _save_tui_run(agent_run)
            status.update(f"Done.{suffix} — saved {run_path}")
        except OSError:
            status.update(f"Done.{suffix}")
        log.write(agent_run.raw_text)
        all_diag = agent_run.tool_diagnostics
        if all_diag:
            notes_title.update("Tool notes")
            notes_body.update(
                "Some tools returned errors or missing sources; see details below.\n\n"
                + "\n".join(all_diag)
            )
        else:
            notes_title.update("")
            notes_body.update("")
        can_export = bool(agent_run.raw_text.strip())
        self.query_one("#export_md", Button).disabled = not can_export
        self.query_one("#export_docx", Button).disabled = not can_export

    def _export_commentary(self, kind: str) -> None:
        if self._agent_run is None:
            self.app.notify("No commentary to export", severity="error")
            return
        dir_raw = self.query_one("#export_dir", Input).value.strip() or "."
        out_dir = Path(dir_raw).expanduser().resolve()
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            self.app.notify(f"Invalid export directory: {error}", severity="error")
            return
        try:
            dest = export_from_run(self._agent_run, format=kind, out_dir=out_dir)
        except (OSError, ValueError) as error:
            self.app.notify(f"Export failed: {error}", severity="error")
            return
        self.app.notify(f"Saved {dest}")


class DeltAgentApp(App[None]):
    TITLE = "DeltAgent"
    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self, initial_csv_path: str | None = None) -> None:
        super().__init__()
        self._initial_csv_path = initial_csv_path

    def on_mount(self) -> None:
        if self._initial_csv_path:
            self.push_screen(VarianceScreen(self._initial_csv_path))
        else:
            self.push_screen(FilePickerScreen(), callback=self._on_csv_chosen)

    def _on_csv_chosen(self, path: str | None) -> None:
        if path:
            self.push_screen(VarianceScreen(path))


def run_tui(initial_csv_path: str | None = None) -> None:
    DeltAgentApp(initial_csv_path=initial_csv_path).run()
