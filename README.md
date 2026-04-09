# DeltAgent

Finance controllers spend 2-4 hours each month writing commentary for the management pack. The numbers are in a spreadsheet, but the reasons sit across Slack, Gmail, Calendar, and CRM threads. DeltAgent pulls those signals together and drafts structured variance commentary ready for review and export.

## Requirements

- Python 3.11+
- `ANTHROPIC_API_KEY` for non-`--dry-run` runs

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
```

For live tools, OAuth, MCP configuration, and environment variables, see [design.md](design.md).

## Quick start

```bash
deltaagent validate tests/fixtures/sample_november_2024.csv --period 2024-11
deltaagent run tests/fixtures/sample_november_2024.csv --period 2024-11 --dry-run
deltaagent tui
deltaagent --help
deltaagent auth mcp-status
```

```text
Detected format: canonical
Significant rows: 3
Insignificant rows: 2
CSV validation passed.
```

```text
Period: November 2024
Bounds: 2024-11-01T00:00:00Z -> 2024-11-30T23:59:59Z
Significant rows: 3
Insignificant rows: 2

Planned tool calls:
- Revenue: search_slack, search_gmail, search_calendar, search_crm
- Salaries: search_slack, search_gmail, search_calendar
- Professional Fees: search_slack, search_gmail, search_calendar
```

## CLI commands

Use `deltaagent --help` for the full command tree, or `deltaagent <command> --help` for one command.

| Command | What it does | Example |
| --- | --- | --- |
| `deltaagent tui [csv_path]` | Opens the interactive terminal UI. If `csv_path` is provided, it starts with that report loaded. | `deltaagent tui tests/fixtures/sample_november_2024.csv` |
| `deltaagent validate <csv_path> [--period <YYYY-MM or Month YYYY>] [--column-map src=dst]` | Checks CSV format and variance rules before running the agent. Use this first to catch data issues early. | `deltaagent validate report.csv --period 2024-11` |
| `deltaagent run <csv_path> --period <YYYY-MM or Month YYYY> [--dry-run] [--column-map src=dst]` | Runs commentary generation for one period. `--dry-run` shows the execution plan without calling the LLM/tools. | `deltaagent run report.csv --period 2024-11 --dry-run` |
| `deltaagent review <runs/run_*.json>` | Opens an interactive review flow for a saved run, where you can accept/edit/flag line-item commentary. | `deltaagent review runs/run_20260409_102219.json` |
| `deltaagent export <runs/run_*.json> [--format md\|docx] [--out-dir <path>]` | Exports a reviewed run to Markdown or DOCX. | `deltaagent export runs/run_20260409_102219.json --format docx --out-dir exports` |
| `deltaagent auth status` | Checks Google auth status. | `deltaagent auth status` |
| `deltaagent auth test` | Runs a Google auth connectivity test. | `deltaagent auth test` |
| `deltaagent auth mcp-status` | Shows configured MCP servers and whether each one is connected. | `deltaagent auth mcp-status` |
| `deltaagent auth mcp-connect --server <name>` | Connects to one MCP server and stores discovered tools for that server. | `deltaagent auth mcp-connect --server salesforce` |

## Project layout

| Path | Role |
| --- | --- |
| `cli.py` | Canonical Typer CLI entrypoint (`deltaagent`) |
| `ui/` | Textual TUI screens and flow |
| `agent/` | Agent loop, prompts, parser, models |
| `tools/` | Tool definitions and mock/live search backends |
| `mcp_client/` | MCP configuration and client registry |
| `exports/` | Markdown and DOCX export |
| `utils/` | Report loading, validation, runtime config |
| `eval/` | Eval cases, runner, and scorecards |
| `auth/` | Provider authentication helpers |
| `tests/` | Test suites and fixtures |
| `design.md` | Architecture and configuration details |
