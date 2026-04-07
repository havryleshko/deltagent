# Variance Commentary Agent

## Problem

**Every month-end a variance commentary for the management accounts. To explain the *why* of the variance numbers are not enough because the context is everywhere - converstaions, calendar tasks, overdues, notes in Slack, CRM etc. reads the numbers, gathers the context, and drafts the full commentary in one run. You can review and export the file. Run in TUI** 

## Requirements

- Python 3.11+
- An [Anthropic](https://www.anthropic.com/) API key (`ANTHROPIC_API_KEY`)

## Setup

```bash
cd deltagent
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the project root (it is gitignored) with your key:

```
ANTHROPIC_API_KEY=sk-ant-...
```

`main.py` loads `.env` via `python-dotenv`. You can also export the variable in your shell instead.

## Run

Always run from the **repository root** so paths like `tests/fixtures/...` resolve.

```bash
python main.py
```

Optional: pass a CSV path to open the variance screen directly (skips the file picker):

```bash
python main.py tests/fixtures/sample_november_2024.csv
```

In the TUI, pick a CSV, confirm the period, run the agent, then export Markdown or Word if you want.

## Configuration

Full list of environment variables, tool backends, and export behaviour: **[design.md](design.md)**.

Short version:


| Topic                 | Notes                                                                                                                                                                                             |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| LLM                   | Default model is `claude-sonnet-4-6` (see `run_agent` in `agent/agent.py`).                                                                                                                       |
| Tools                 | Default `DELTAGENT_TOOL_MODE=mock` uses fixture data under `tests/fixtures/`. Set `DELTAGENT_TOOL_MODE=live` and provider credentials for real Gmail, Calendar, Slack, HubSpot (see `design.md`). |
| Thresholds / currency | Optional: `DELTAGENT_SIGNIFICANCE_PCT`, `DELTAGENT_SIGNIFICANCE_ABS`, `DELTAGENT_CURRENCY_SYMBOL` (see `design.md`).                                                                              |


## Tests

```bash
python3 -m pytest tests/
```

Optional live API checks: set `DELTAGENT_RUN_LIVE_INTEGRATION_TESTS=1` and the required service tokens; see `tests/test_phase6_integration.py`.

## Project layout


| Path        | Role                                                    |
| ----------- | ------------------------------------------------------- |
| `main.py`   | Entry: Textual TUI                                      |
| `ui/app.py` | Screens (file pick, variance table, commentary, export) |
| `agent/`    | Anthropic tool loop and prompts                         |
| `tools/`    | `search_*` tools (mock or live)                         |
| `utils/`    | CSV validation and env config                           |
| `exports/`  | Markdown / `.docx` writers                              |
| `design.md` | Product and architecture source of truth                |


