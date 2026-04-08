# Case 01 — Xero Demo, March 2026

**Purpose:** Baseline Xero export. Tests that the agent correctly handles a single revenue overperformance with a direct cost follow-through, citing Slack, Gmail, Calendar, and CRM evidence.

**What makes this case interesting:**
- Revenue (Sales) is significantly over budget (+83%) due to a single enterprise deal pulled forward from April.
- Purchases are over as a direct result of the revenue outperformance — the agent should make this connection explicit rather than treating them as independent events.
- Most other lines are insignificant; the agent should enumerate them briefly without fabricating reasons.

**Thresholds:** pct=10%, abs=£500 — appropriate for a small UK company with low absolute spend on many lines.

**Evidence profile:**
- Sales: rich evidence across all four tools (Slack, Gmail, Calendar, CRM)
- Purchases: Slack and Gmail explain the COGS variance clearly

**What a good output looks like:**
- Sales commentary names the Meridian contract, pull-forward date, and CFO approval
- Purchases commentary links the cost increase directly to the revenue overperformance
- Sources cited per line
- No fabricated reasons for insignificant lines
