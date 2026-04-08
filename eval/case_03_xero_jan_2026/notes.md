# Case 03 — Xero Demo, January 2026

**Purpose:** Tests the agent on an extreme positive revenue variance (+1,024%) against a very low budget. Tests whether the agent correctly contextualises the variance (low budget denominator + Q4 carry-over), avoids sensationalising the percentage, and handles zero-budget lines gracefully.

**What makes this case interesting:**
- Sales is the only significant variance — £5,121 above a £500 budget (+1,024%). This is extreme on percentage terms but explainable: the £500 budget was a conservative January placeholder, and Q4 2025 deals slipped into January.
- Most other lines have zero budget (budgets not set for January, typical for this company's planning process). The actual spend is real but the percentage variance is meaningless. The agent should NOT treat these as significant.
- Subscriptions: £1,220 actual vs £0 budget — large absolute amount but pct=0 (budget=0), so NOT significant by threshold logic. Watch whether the agent mistakenly flags this.
- This is a precision test: the agent must reason about what the numbers mean, not just recite them.

**Thresholds:** pct=10%, abs=£500

**What a good output looks like:**
- Sales commentary contextualises the percentage clearly — "against a £500 conservative placeholder budget, not a meaningful plan"
- Names the three Q4 carry-over deals (Redwood, Apex, Fortis) from CRM evidence
- Notes the CFO sign-off
- Does NOT flag Subscriptions, Rent, or other zero-budget lines as significant
