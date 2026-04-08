# Case 07 — Synthetic, October 2024 — Revenue Miss

**Purpose:** Tests the agent on a negative revenue variance where evidence comes primarily from CRM + Slack. This is the most commercially important case in the eval set — the agent must correctly identify deal slippage vs permanent loss, and connect the Cost of Revenue underspend as a natural consequence.

**What makes this case interesting:**
- Revenue (-$82,000, -16.4%): Three deals slipped, one lost. The agent must distinguish between slippage (recoverable, in November forecast) and loss (permanent). CRM data is rich on deal-level detail.
- Professional Services (-$6,000, -12%): Directly downstream of the revenue slips — PS SOWs are tied to software deal close dates. The agent should make this linkage explicit.
- Cost of Revenue (-$12,000, -15%): Underspend is mechanically connected to fewer customer onboardings. The agent should explain this as a consequence, not a separate managed saving.
- Software Licenses (-$3,000, -10%): Right on the 10% threshold — NOT significant (10% is not strictly greater than 10%). Watch whether the agent misclassifies this.
- Support Contracts: NOT significant (+2.5%).

**Evidence profile:**
- CRM is the primary evidence source (all three significant lines have CRM evidence)
- Slack provides narrative colour for Revenue and Professional Services
- No Gmail/Calendar evidence — the agent should not hallucinate it

**What a good output looks like:**
- Revenue: names all four deals by name with correct dollar amounts, clearly separates slipped vs lost, flags November recovery plan
- Professional Services: explicitly links the miss to the software deal timing, not a separate issue
- Cost of Revenue: explains as a mechanical consequence of reduced onboardings
- No fabricated Gmail or Calendar evidence
