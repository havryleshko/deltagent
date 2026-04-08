# Case 05 — Synthetic, February 2026 — Marketing Campaign Timing

**Purpose:** Tests the agent on offsetting variances within a single department. Digital Advertising is significantly over because a campaign was pulled forward; Events is significantly under because the Sales Summit was postponed to April. The agent should connect these as related period timing events rather than independent overruns and savings.

**What makes this case interesting:**
- Digital Advertising (+$28,500, +57%): Full Q2 campaign budget pulled forward to February — March digital line will be $0. This is a timing reallocation, not a budget overrun. The agent should explicitly note the net quarterly impact.
- Events & Conferences (-$5,500, -27.5%): Sales Summit moved to April — this is a saving in February but will show as an overrun in April. The agent should flag the April impact.
- Content & Creative (+$1,200, +15%): January strategy work billed in February — minor but significant by thresholds.
- Marketing Software and PR & Comms are NOT significant.
- This case tests whether the agent can reason about the net budget impact across periods.

**Evidence profile:**
- All three significant lines have Slack + Gmail + Calendar evidence
- Campaign pull-forward is well-documented

**What a good output looks like:**
- Digital Advertising: explains pull-forward clearly, notes March digital = $0, net Q1 digital on plan
- Events: explains summit postponement, flags April reforecast needed
- Content: explains January work billed in February, notes it's a one-month artefact
