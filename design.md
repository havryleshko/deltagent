# Variance Commentary Agent — System Design

---

## Problem

Every month-end, a finance controller spends 2–4 hours writing variance commentary for the management accounts pack. The numbers are in a spreadsheet. The problem is that the context that explains the variance is everywhere — conversations, calendar tasks, overdues, notes in Slack, CRM etc. This agent gathers as much context as possible from email, CRM, and comms, and given your month-end close it explains the *why* of the variance. It reads the numbers, gathers the context, and drafts the full commentary in one run. You review and export the file.

---

## User

Finance Controller or FP&A analyst at a $10M–$300M business. Runs this once a month at close.

---

## Input / Output

### Input (required)

CSV file with columns:


| Column         | Description                                           |
| -------------- | ----------------------------------------------------- |
| `period`       | e.g. `"November 2024"`                                |
| `line_item`    | e.g. `"Revenue"`, `"Salaries"`, `"Professional Fees"` |
| `budget_usd`   | Budgeted figure                                       |
| `actual_usd`   | Actual figure                                         |
| `variance_usd` | Actual minus budget                                   |
| `variance_pct` | Percentage variance                                   |


### Output

- Plain English commentary per significant line item, with traceable sources per line
- Executive summary paragraph for the full period
- Export as `.docx` (board packs) or `.md` (Notion/Confluence)

### What "significant" means

Default: variance > 10% AND > $1,000 absolute. Configurable via environment config.

---

## Flow

Two entry points — CLI and TUI — both call the same agent core.

### CLI (primary)

```bash
deltaagent run report.csv
deltaagent run report.csv --dry-run
deltaagent review runs/run_20251130_143022.json
deltaagent export runs/run_20251130_143022.json

```

`run` is the main path. It should infer the period when the file is clear, and only require `--period` when the file is ambiguous.

### TUI (interactive wrapper)

1. User launches app
2. TUI opens
3. User selects CSV via file picker
4. Variance table renders, user confirms period
5. User presses Run — calls `run_agent()` directly, same as CLI
6. Agent fires tool calls in parallel for significant lines
7. Tool results return, agent synthesises
8. Full commentary renders with sources per line
9. User reviews (Accept / Edit / Regenerate / Flag) and exports

---

## Architecture

```
main.py
│
├── cli.py                     Typer CLI — all commands
│
├── ui/app.py                  Textual TUI — calls run_agent(), same as CLI
│   ├── FilePickerScreen       Select CSV
│   ├── VarianceScreen         Show table, confirm period, run
│   └── CommentaryScreen       Display output, export
│
├── agent/
│   ├── agent.py               run_agent() — plain async fn, no Textual deps
│   ├── parser.py              Tolerant parser — model text → AgentResult dataclass
│   └── prompts.py             System prompt + message builder
│
├── tools/
│   ├── definitions.py         Tool schemas
│   ├── base.py                ToolResult + Evidence dataclasses
│   ├── slack_tool.py          Mock (fixture-backed)
│   ├── gmail_tool.py          Gmail API — date-bounded queries
│   ├── calendar_tool.py       Google Calendar API — date-bounded queries
│   └── crm_tool.py            Mock (fixture-backed)
│
├── auth/
│   ├── gmail.py               login(), status(), test(), refresh()
│   └── calendar.py            login(), status(), test(), refresh()
│
├── utils/
│   └── csv_validator.py       Schema + type validation
│
├── runs/                      Persisted AgentResult JSON files
│
└── exports/
    └── exporter.py            Renders from AgentResult dataclass — not raw string

```

---

## Stack


| Layer            | Choice                   | Why                                      |
| ---------------- | ------------------------ | ---------------------------------------- |
| LLM              | Claude via Anthropic SDK | Native tool calling, no framework needed |
| Model            | `claude-sonnet-4-6`      | Best reasoning for finance commentary    |
| CLI              | Typer                    | Clean command surface, composable output |
| TUI              | Textual                  | Python-native, clean terminal UI         |
| Tool calling     | `asyncio.gather`         | Speed — all 4 tools fire simultaneously  |
| Gmail + Calendar | Google API Python client | OAuth, read-only scopes                  |
| Slack            | Mock (fixtures)          | Until real credentials available         |
| CRM              | Mock (fixtures)          | Until real credentials available         |
| Export           | python-docx + markdown   | `.docx` for board packs, `.md` for wikis |


---

## Agent Design

Single agent. No orchestration framework. The Anthropic SDK handles the tool-calling loop natively.

```python
client = AsyncAnthropic()

while stop_reason == "tool_use":
    tool_calls = extract_tool_calls(response)
    results = await asyncio.gather(*[execute(t) for t in tool_calls])
    messages.append(tool_results)
    response = await client.messages.create(...)

return AgentResult  # structured dataclass, not raw string

```

All tool calls are hard date-bounded to the reporting period. No tool infers dates.

---

## Tool Calling Rules (system prompt)

- Only call tools for significant variances
- CRM: revenue lines only
- Gmail: salary, headcount, large one-off costs
- Slack: operational context on any line
- Calendar: timing variances (marketing, travel, events)
- Fire all relevant tools in parallel, never sequentially
- If a tool returns an error, proceed without it — mark the gap visibly

---

## Tool Definitions


| Tool              | Finds                                              | Does NOT find                      |
| ----------------- | -------------------------------------------------- | ---------------------------------- |
| `search_slack`    | Operational chat, team decisions, informal updates | Formal approvals, deal data        |
| `search_gmail`    | CFO approvals, invoices, contract decisions        | Casual chat, deal pipeline         |
| `search_calendar` | Bank holidays, offsites, campaign launches         | Why a deal slipped, cost approvals |
| `search_crm`      | Deals closed/slipped, pipeline, revenue drivers    | Any cost line data                 |


---

## Output Structure

```
AgentResult
├── period, currency, run_id
├── executive_summary
├── line_items: list[LineItem]
│   ├── header, delta, delta_pct, commentary
│   ├── sources: list[Evidence]      ← message ID, timestamp, snippet per hit
│   ├── review_status                ← pending | accepted | edited | flagged
│   └── edited_commentary
├── insignificant: list[str]
└── gaps: list[str]                  ← lines with no supporting evidence

```

---

## Commentary Format

```
EXECUTIVE SUMMARY
[2-3 sentences covering the period overall]

LINE COMMENTARY

Revenue | Budget: $100,000 | Actual: $115,000 | Variance: +$15,000 (+15%)
[Paragraph explaining why]

Sources
- Slack #finance-ops — 2025-11-14 09:32 — "Q4 campaign approved..."
- Gmail: "RE: November revenue" — 2025-11-28

---

INSIGNIFICANT VARIANCES
Software & Subscriptions: $200 over (4%) — within normal range

```

### Style rules (system prompt)

- State variance amount and direction first
- Give reason second
- Mark inferred reasons: `(inferred — no source found)`
- Never fabricate a reason — say `"No context found — recommend review"` if blank
- Professional tone, written for a CEO not an accountant

---

## Review Workflow

After run completes, state persists to `runs/run_YYYYMMDD_HHMMSS.json`.

`deltaagent review runs/run_001.json` opens a per-line loop:

```
LINE: Marketing Spend | Δ +$42,000 | +18.4%
Commentary: Increase driven by Q4 campaign spend approved 14 Nov...
Sources: Slack #finance-ops 2025-11-14, Gmail "RE: Q4 budget" 2025-11-09

[A]ccept  [E]dit  [R]egenerate  [F]lag  [S]kip

```

Sessions survive interruption. Re-running `review` resumes from the first non-decided item. `deltaagent export` assembles the final doc from accepted and edited lines only.

---

## Mock Data Strategy

Slack and CRM are mocked until real credentials are available. Mocks return `ToolResult` envelopes with plausible fixture IDs and timestamps. Gmail and Calendar are wired to real APIs with hard date-bounded queries.

```
tests/fixtures/
├── mock_slack_responses.json
├── mock_crm_responses.json
└── sample_november_2024.csv

```

---

## Export


| Format  | Use case                           | Library          |
| ------- | ---------------------------------- | ---------------- |
| `.docx` | Board packs, formal reporting      | python-docx      |
| `.md`   | Notion, Confluence, internal wikis | Plain text write |


Output filename: `variance_commentary_November_2024.docx` Rendered from `AgentResult` dataclass, not raw model string.

---

## Environment Variables

```bash
ANTHROPIC_API_KEY=

DELTAGENT_TOOL_MODE=mock        # mock | live
DELTAGENT_SIGNIFICANCE_PCT=10
DELTAGENT_SIGNIFICANCE_ABS=1000
DELTAGENT_CURRENCY_SYMBOL=$

GOOGLE_CREDENTIALS_PATH=credentials.json
GOOGLE_TOKEN_PATH=token.json

SLACK_BOT_TOKEN=
HUBSPOT_PRIVATE_APP_TOKEN=
HUBSPOT_API_KEY=

DELTAGENT_RUN_LIVE_INTEGRATION_TESTS=

```

---

## Build Order


| Phase | What                                       | Done when                                                    |
| ----- | ------------------------------------------ | ------------------------------------------------------------ |
| 1     | Agent core                                 | CSV in → commentary out, no tools, no TUI                    |
| 2     | Mock tools                                 | All 4 tools return fixture data, commentary has real reasons |
| 3     | TUI                                        | File picker + variance table + commentary display            |
| 4     | Export                                     | `.docx` and `.md` working                                    |
| 5     | Polish                                     | Threshold config, period confirmation, error messages        |
| 6     | Real tools                                 | Gmail + Calendar OAuth, Slack, CRM                           |
| A     | CLI + trustworthy output + review workflow | Controller can run, review, and export without the TUI       |


---

## What success looks like

User runs `deltaagent run report.csv`, reviews commentary with `deltaagent review`, and exports with `deltaagent export`. 60 seconds later, a `.docx` file exists — with sources per line — that a Finance Controller could put directly into a board pack with minor edits. If the file is ambiguous, the CLI stops and gives the exact rerun fix. That is the whole product.