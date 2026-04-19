# DeltAgent

Finance controllers spend 2-4 hours each month writing commentary for the management pack. The numbers are in a spreadsheet, but the reasons sit across Slack, Gmail, Calendar, and CRM threads. DeltAgent pulls those signals together and drafts structured variance commentary ready for review and export.

## Requirements

- Python 3.11+
- `ANTHROPIC_API_KEY` for non-`--dry-run` runs

`pip install -e .` pulls in `openpyxl`, which is required to load `.xlsx` budget exports.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
```

Local Homebrew install:

```bash
brew install --build-from-source ./Formula/deltaagent.rb
```

Planned tap install once the formula is published:

```bash
brew tap havryleshko/tap
brew install deltaagent
```

For live tools, OAuth, MCP configuration, and environment variables, see [design.md](design.md).

## Report inputs

- **CSV** — canonical management-pack style exports (see `tests/fixtures/sample_november_2024.csv`).
- **Excel** — `.xlsx` in the bundled “Budget Variance” layout (company title row, `1 November 2024` style period in `A3`, header `Account` / `Actual` / `Budget`, data from row 6). The eval workbooks under `evals/` match this shape.

`validate` / `run` / `tui` accept either format; pass the file path as the positional argument.

For **live** Slack/Gmail/Calendar/CRM search, use Google OAuth as described in `design.md` and leave `DELTAGENT_TOOL_MODE` unset or set it to `live`. In **`mock`** mode (`DELTAGENT_TOOL_MODE=mock`), tools read `tests/fixtures/mock_context_november_2024.json` by default — not per-bundle `evals/**.mock_context.json`. To score or replay a specific bundle with its own mock payload, use the round eval scripts under `evals/` (they set the fixture path before calling the agent).

## Quick start

```bash
deltaagent run tests/fixtures/sample_november_2024.csv --dry-run
deltaagent run tests/fixtures/sample_november_2024.csv
deltaagent review runs/run_20260409_102219.json
deltaagent export runs/run_20260409_102219.json --format docx --out-dir exports
deltaagent tui
deltaagent --help
deltaagent auth mcp-status
```

Example on a bundled November 2024 workbook (live tools recommended so line items can match real sources):

```bash
deltaagent run evals/round5/aurora_education_services_november_2024.xlsx --dry-run
deltaagent run evals/round5/aurora_education_services_november_2024.xlsx
```

## Bundled eval workbooks (Round 5)

Ten synthetic companies live in `evals/round5/` as `*.xlsx` plus matching `*.mock_context.json` and `*.oracle.json`, listed in `evals/round5/manifest.json`. Regenerate files from specs with:

```bash
PYTHONPATH=. python3 evals/round5/build_round5_eval_bundles.py
```

```text
Detected format: canonical
Significant rows: 3
Insignificant rows: 2
CSV validation passed.
```

```text
Detected format: canonical
Period: November 2024
Bounds: 2024-11-01T00:00:00Z -> 2024-11-30T23:59:59Z
Significant rows: 3
Insignificant rows: 2

Planned tool calls:
- Revenue: search_slack, search_gmail, search_calendar, search_crm
- Salaries: search_slack, search_gmail, search_calendar
- Professional Fees: search_slack, search_gmail, search_calendar

Run for real: deltaagent run tests/fixtures/sample_november_2024.csv
```

## CLI commands

Use `deltaagent --help` for the full command tree, or `deltaagent <command> --help` for one command.

| Command | What it does | Example |
| --- | --- | --- |
| `deltaagent tui [path]` | Opens the interactive terminal UI. If a report path is provided, it starts with that file loaded. | `deltaagent tui tests/fixtures/sample_november_2024.csv` |
| `deltaagent validate <path> [--period <YYYY-MM or Month YYYY>] [--column-map src=dst]` | Checks whether DeltAgent can read the file and split significant vs insignificant variances. Use this when you want to debug an import. | `deltaagent validate report.csv` |
| `deltaagent run <path> [--period <YYYY-MM or Month YYYY>] [--dry-run] [--column-map src=dst]` | Main command. It validates the file, infers the period when the file is clear, and runs commentary generation. Add `--period` only if DeltAgent asks for it. | `deltaagent run report.csv --dry-run` |
| `deltaagent review <runs/run_*.json>` | Opens an interactive review flow for a saved run, where you can accept/edit/flag line-item commentary. | `deltaagent review runs/run_20260409_102219.json` |
| `deltaagent export <runs/run_*.json> [--format md\|docx] [--out-dir <path>]` | Exports a reviewed run to Markdown or DOCX. | `deltaagent export runs/run_20260409_102219.json --format docx --out-dir exports` |
| `deltaagent auth status` | Checks Google auth status. | `deltaagent auth status` |
| `deltaagent auth test` | Runs a Google auth connectivity test. | `deltaagent auth test` |
| `deltaagent auth mcp-status` | Shows configured MCP servers and whether each one is connected. | `deltaagent auth mcp-status` |
| `deltaagent auth mcp-connect --server <name>` | Connects to one MCP server and stores discovered tools for that server. | `deltaagent auth mcp-connect --server salesforce` |

`run` is the default path. If the file shape is clear, DeltAgent will infer the period and continue. If the file is ambiguous, it stops and tells you the exact `--period` or `--column-map` fix to rerun with.

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
| `evals/` | Seeded workbooks, mock contexts, oracles, and round runners (`run_round*.py`, `oracle_scorer.py`) |
| `auth/` | Provider authentication helpers |
| `tests/` | Test suites and fixtures |
| `design.md` | Architecture and configuration details |

## License

MIT — see [LICENSE](LICENSE).
