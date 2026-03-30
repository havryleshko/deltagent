# Variance Commentary Agent — System Design

## Problem
Every month-end, a finance controller spends 2–4 hours writing variance commentary
for the management accounts pack. The numbers are in a spreadsheet. The reasons are
in their head, in emails, in Slack, in the CRM. Writing the commentary means
pulling all of that together manually, under deadline pressure.

**This tool eliminates the blank page.** It reads the numbers, gathers the context,
and drafts the full commentary in one run. The human reviews and exports.

---

## User
Finance Controller or FP&A analyst at a £10M–£300M business.
Runs this once a month at close. Not a developer.

---

## Input / Output

**Input (required)**
- CSV file with columns:
  - `period` — e.g. "November 2024"
  - `line_item` — e.g. "Revenue", "Salaries", "Professional Fees"
  - `budget_gbp` — budgeted figure
  - `actual_gbp` — actual figure
  - `variance_gbp` — actual minus budget
  - `variance_pct` — percentage variance

**Output**
- Plain English commentary per significant line item
- Executive summary paragraph for the full period
- Export as `.docx` (board packs) or `.md` (Notion/Confluence)

**What "significant" means**
Default: variance > 10% AND > £1,000 absolute. Configurable.

---

## Flow

```
1. User launches app: python main.py
2. Textual TUI opens
3. User selects CSV via file picker
4. Variance table renders — user confirms period
5. User presses Run
6. Agent fires 4 tool calls IN PARALLEL:
   - Slack: operational context
   - Gmail: formal approvals and decisions
   - Calendar: timing anomalies
   - CRM: revenue and deal pipeline
7. Tool results return, agent synthesises
8. Full commentary renders in terminal
9. User selects export format and saves file
```

---

## Architecture

```
main.py
│
├── ui/app.py                  Textual TUI
│   ├── FilePickerScreen       Select CSV
│   ├── VarianceScreen         Show table, confirm period, run
│   └── CommentaryScreen       Display output, export
│
├── agent/
│   ├── agent.py               Anthropic SDK tool-calling loop
│   └── prompts.py             System prompt + message builder
│
├── tools/
│   ├── definitions.py         Tool schemas (critical for accuracy)
│   ├── slack_tool.py          Slack SDK or mock
│   ├── gmail_tool.py          Gmail API
│   ├── calendar_tool.py       Google Calendar API
│   └── crm_tool.py            HubSpot / Salesforce or mock
│
└── exports/
    └── exporter.py            .docx and .md writers
```

---

## Stack

| Layer | Choice | Why |
|---|---|---|
| LLM | Claude via Anthropic SDK | Native tool calling, no framework needed |
| Model | claude-opus-4-5 | Best reasoning for finance commentary |
| TUI | Textual | Python-native, clean terminal UI |
| Tool calling | Parallel via asyncio.gather | Speed — all 4 tools fire simultaneously |
| Gmail + Calendar | Google API Python client | OAuth, read-only scopes |
| Slack | Slack SDK | search_messages API |
| CRM | HubSpot API or mock | Deal pipeline for revenue lines |
| Export | python-docx + markdown | .docx for board packs, .md for wikis |

---

## Agent Design

**Single agent. No orchestration framework.**
The Anthropic SDK handles the tool-calling loop natively.

```
while stop_reason == "tool_use":
    tool_calls = extract_tool_calls(response)
    results = await asyncio.gather(*[execute(t) for t in tool_calls])
    messages.append(tool_results)
    response = client.messages.create(...)

return response.text  # final commentary
```

**Tool calling rules (in system prompt):**
- Only call tools for significant variances
- CRM: revenue lines only
- Gmail: salary, headcount, large one-off costs
- Slack: operational context on any line
- Calendar: timing variances (marketing, travel, events)
- Fire all relevant tools in parallel, never sequentially
- If a tool returns an error, proceed without it

---

## Tool Definitions (summary)

Each tool has a precise description telling Claude what it is AND what it is not for.
Vague descriptions = wrong tool calls = wrong commentary.

| Tool | Finds | Does NOT find |
|---|---|---|
| `search_slack` | Operational chat, team decisions, informal updates | Formal approvals, deal data |
| `search_gmail` | CFO approvals, invoices, contract decisions | Casual chat, deal pipeline |
| `search_calendar` | Bank holidays, offsites, campaign launches | Why a deal slipped, cost approvals |
| `search_crm` | Deals closed/slipped, pipeline, revenue drivers | Any cost line data |

---

## Commentary Format

```
EXECUTIVE SUMMARY
[2-3 sentences covering the period overall]

LINE COMMENTARY

Revenue | Budget: £100,000 | Actual: £115,000 | Variance: +£15,000 (+15%)
[Paragraph explaining why]

---

Professional Fees | Budget: £8,000 | Actual: £14,000 | Variance: -£6,000 (-75%)
[Paragraph explaining why]

---

INSIGNIFICANT VARIANCES
Software & Subscriptions: £200 over (4%) — within normal range
Office & Facilities: £100 over (2.5%) — within normal range
```

**Style rules (in system prompt):**
- State variance amount and direction first
- Give reason second
- Mark inferred reasons: "(inferred — no source found)"
- Never fabricate a reason — say "No context found — recommend review" if blank
- Professional tone, written for a CEO not an accountant

---

## Mock Data Strategy (for development)

Slack and CRM are mocked until real credentials are available.
Mocks return fixtures that align with `sample_november_2024.csv`.

```
tests/fixtures/
├── mock_slack_responses.json     # Messages explaining salary + professional fees variance
├── mock_crm_responses.json       # Deals explaining revenue overperformance
└── sample_november_2024.csv      # The numbers
```

Mock files match the CSV so commentary is coherent end-to-end.
Gmail + Calendar are wired to real APIs from day one.

---

## Export

| Format | Use case | Library |
|---|---|---|
| `.docx` | Board packs, formal reporting | python-docx |
| `.md` | Notion, Confluence, internal wikis | Plain text write |

Output filename: `variance_commentary_November_2024.docx`

---

## Environment Variables

```
ANTHROPIC_API_KEY=

# Google (Gmail + Calendar — same OAuth flow)
GOOGLE_CREDENTIALS_PATH=credentials.json
GOOGLE_TOKEN_PATH=token.json

# Slack (when available)
SLACK_BOT_TOKEN=

# CRM — one of:
HUBSPOT_API_KEY=
SALESFORCE_USERNAME=
SALESFORCE_PASSWORD=
SALESFORCE_SECURITY_TOKEN=
```

---

## Build Order

| Phase | What | Done when |
|---|---|---|
| 1 | Agent core | CSV in → commentary out, no tools, no TUI. Just `python agent/agent.py` |
| 2 | Mock tools | Slack + CRM return fixture data. Commentary has real reasons |
| 3 | Real tools | Gmail + Calendar wired. Google OAuth working |
| 4 | TUI | Textual file picker + variance table + commentary display |
| 5 | Export | .docx and .md working |
| 6 | Polish | Threshold config, period confirmation, error messages |

**Rule: Phase 1 must produce good commentary before touching anything else.**
The agent prompt and tool definitions are the product. Everything else is plumbing.

---

## What success looks like

User runs `python main.py`, selects `november_2024.csv`, presses Run.
60 seconds later, a `.docx` file exists that a Finance Controller could paste
directly into a board pack with minor edits. That is the whole product.