# Variance Commentary Agent — System Design

## Problem

Every month-end, a finance controller spends 2–4 hours writing variance commentary for the management accounts pack. The numbers are in a spreadsheet. The problem is that the context that explains the variance is everywhere - converstaions, calendar tasks, overdues, notes in Slack, CRM etc. **This agent is for gathering as much context via from email, CRM etc. as possible and given your month-end close it explains *why* of the variance. It reads the numbers, gathers the context, and drafts the full commentary in one run. You can review and export the file**

---

## User

Finance Controller or FP&A analyst at a $10M–$300M business. Runs this once a month at close.

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
Default: variance > 10% AND > $1,000 absolute; configurable

---

## Flow

1. User launches app - terminal UI (Textual)
2. TUI opens
3. User selects CSV via file picker
4. Variance table renders, user confirms period
5. User presses Run
6. Agent assesses variance complexity, then fires tool calls IN PARALLEL:
  - Slack: operational context (any significant line)
  - Gmail: formal approvals and decisions (salary, headcount, large one-offs)
  - Calendar: timing anomalies (marketing, travel, events)
  - CRM: revenue and deal pipeline (ONLY if revenue line is significant)
   Each tool queries broad first, narrows only if first pass returns nothing.
7. Tool results return, agent synthesises
8. Full commentary renders in terminal
9. User selects export format and saves file

---

## Architecture

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
├── utils/
│   └── csv_validator.py       Schema + type validation
│
└── exports/
    └── exporter.py            .docx and .md writers

## Stack


| Layer            | Choice                      | Why                                      |
| ---------------- | --------------------------- | ---------------------------------------- |
| LLM              | Claude via Anthropic SDK    | Native tool calling, no framework needed |
| Model            | claude-sonnet-4-6           | Best reasoning for finance commentary    |
| TUI              | Textual                     | Python-native, clean terminal UI         |
| Tool calling     | Parallel via asyncio.gather | Speed — all 4 tools fire simultaneously  |
| Gmail + Calendar | Google API Python client    | OAuth, read-only scopes                  |
| Slack            | Slack SDK                   | search_messages API                      |
| CRM              | HubSpot API or mock         | Deal pipeline for revenue lines          |
| Export           | python-docx + markdown      | .docx for board packs, .md for wikis     |


---

## Agent Design

**Single agent. No orchestration framework.**
The Anthropic SDK handles the tool-calling loop natively.

```
client = AsyncAnthropic()

while stop_reason == "tool_use":
    tool_calls = extract_tool_calls(response)
    results = await asyncio.gather(*[execute(t) for t in tool_calls])
    messages.append(tool_results)
    response = await client.messages.create(...)

return response.text
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


| Tool              | Finds                                              | Does NOT find                      |
| ----------------- | -------------------------------------------------- | ---------------------------------- |
| `search_slack`    | Operational chat, team decisions, informal updates | Formal approvals, deal data        |
| `search_gmail`    | CFO approvals, invoices, contract decisions        | Casual chat, deal pipeline         |
| `search_calendar` | Bank holidays, offsites, campaign launches         | Why a deal slipped, cost approvals |
| `search_crm`      | Deals closed/slipped, pipeline, revenue drivers    | Any cost line data                 |


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


| Format  | Use case                           | Library          |
| ------- | ---------------------------------- | ---------------- |
| `.docx` | Board packs, formal reporting      | python-docx      |
| `.md`   | Notion, Confluence, internal wikis | Plain text write |


Output filename: `variance_commentary_November_2024.docx`

---

## Environment Variables

```
ANTHROPIC_API_KEY=

# Tool backends: mock (default) uses tests/fixtures; live calls real APIs when credentials are set
DELTAGENT_TOOL_MODE=mock
# DELTAGENT_TOOL_MODE=live

# Phase 5 — significance and display (optional)
DELTAGENT_SIGNIFICANCE_PCT=10
DELTAGENT_SIGNIFICANCE_ABS=1000
DELTAGENT_CURRENCY_SYMBOL=$

# Google (Gmail + Calendar — same OAuth flow, read-only scopes)
GOOGLE_CREDENTIALS_PATH=credentials.json
GOOGLE_TOKEN_PATH=token.json

# Slack (live: search.messages; often needs a user token with search:read)
SLACK_BOT_TOKEN=

# CRM — HubSpot private app token preferred (live lists deals, filters by close month)
HUBSPOT_PRIVATE_APP_TOKEN=
HUBSPOT_API_KEY=

# Optional Salesforce env (not implemented; use HubSpot for live CRM)
SALESFORCE_USERNAME=
SALESFORCE_PASSWORD=
SALESFORCE_SECURITY_TOKEN=

# Run tests/test_phase6_integration.py only when set to 1
DELTAGENT_RUN_LIVE_INTEGRATION_TESTS=
```

---

## Build Order


| Phase | What       | Done when                                                    |
| ----- | ---------- | ------------------------------------------------------------ |
| 1     | Agent core | CSV in → commentary out, no tools, no TUI                    |
| 2     | Mock tools | All 4 tools return fixture data. Commentary has real reasons |
| 3     | TUI        | File picker + variance table + commentary display            |
| 4     | Export     | .docx and .md working                                        |
| 5     | Polish     | Threshold config, period confirmation, error messages        |
| 6     | Real tools | Gmail + Calendar OAuth, Slack, CRM                           |


**Rule: Phase 1 must produce good commentary before touching anything else.**
The agent prompt and tool definitions are the product. Everything else is plumbing.

---

## What success looks like

User runs `python main.py`, selects `november_2024.csv`, presses Run.
60 seconds later, a `.docx` file exists that a Finance Controller could paste
directly into a board pack with minor edits. That is the whole product.