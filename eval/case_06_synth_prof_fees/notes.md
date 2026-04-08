# Case 06 — Synthetic, November 2024 — Professional Fees Spike

**Purpose:** Tests the agent on a concentrated, non-recurring cost event driven by a single large invoice (IP litigation advisory). Evidence is primarily email-only — tests whether the agent correctly builds its case from Gmail evidence alone.

**What makes this case interesting:**
- Professional Fees (+$27,500, +183%): Single invoice from outside IP counsel for an active patent dispute. The agent needs to explain the full context (Vantec claim, USPTO proceedings, multi-month matter with remaining Q1 exposure).
- Legal & Compliance (+$1,200, +24%): Smaller but significant — two VP employment agreement reviews. Standard work but correctly in scope.
- Audit & Accounting and other lines are NOT significant.
- Evidence is concentrated in Gmail (no Slack/Calendar/CRM for Professional Fees beyond what's there).
- This case tests evidence accuracy: the agent should NOT hallucinate Slack messages for Professional Fees just because they're absent.

**What a good output looks like:**
- Professional Fees: names the matter (WA-2024-IP-441), the opposing party (Vantec Corp), the law firm (Whitmore & Associates), the USPTO timeline, and the Q1 remaining exposure ($8–18K)
- Legal & Compliance: names the two VP hires, notes the fixed MSA rate
- No fabricated Slack/Calendar evidence for lines where it doesn't exist
