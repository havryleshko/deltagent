# Case 04 — Synthetic, November 2024 — Headcount Variances

**Purpose:** Tests the agent on a complex headcount month with 6 significant lines, each with a different character. This is the most complex case in the eval set — it tests the agent's ability to maintain clarity across multiple concurrent explanations and avoid conflating unrelated variances.

**What makes this case interesting:**
- 6 significant lines, each with a distinct explanation (new hire, overlap, bonus mis-posting, seasonal temps, contractor, finance support)
- Contractor Spend is the largest single variance (+$18,500, +92.5%) — platform migration
- Benefits & Payroll Taxes is NOT significant at 8% despite $4,000 overage — tests threshold handling
- Sales Salaries is NOT significant at 4% despite $6,000 overage — tests threshold handling
- G&A Salaries and Marketing Salaries are borderline (13.3% and 14%) — correctly in scope

**Evidence profile:**
- Engineering, Product, Marketing, Operations, G&A, Contractors all have Slack evidence
- Contractor Spend also has Gmail (SOW + extension) and CRM (project status)
- Benefits & Payroll Taxes has no mock evidence (correct — it shouldn't be significant)

**What a good output looks like:**
- Each of the 6 significant lines gets a separate, accurate explanation
- Agent connects contractor spend to the platform migration project (citing project name and CTO approval)
- Agent flags the Marketing bonus coding error as a recommended reclassification
- Agent does NOT explain Sales Salaries or Benefits lines (below threshold)
