# Phase B Eval Scorecard

Score each case on five dimensions (0–3 per dimension, 0 = fail, 1 = partial, 2 = good, 3 = excellent).


| Dimension         | Description                                                           |
| ----------------- | --------------------------------------------------------------------- |
| Factual alignment | Numbers in commentary match the CSV exactly                           |
| Hallucination     | No invented evidence, people, deals, or events                        |
| Coverage          | All significant lines addressed, insignificant handled correctly      |
| Tone & format     | Board-pack register, correct structure, concise                       |
| Source quality    | Sources cited are from the fixture; quality matches evidence richness |


---

## Case 01 — Xero Demo, March 2026

Run ID: `run_20260407_145755`
Date: 2026-04-07


| Dimension         | Score (0–3) | Notes |
| ----------------- | ----------- | ----- |
| Factual alignment | 2           | Sales and Purchases match the CSV, but the revenue bridge goes beyond what is cleanly reconciled in the fixture. |
| Hallucination     | 2           | Claims mostly track Slack, Gmail, and CRM, but the residual revenue explanation is more interpretive than directly grounded. |
| Coverage          | 2           | Both significant lines are covered, but the case was meant to exercise Calendar evidence and the run never uses it. |
| Tone & format     | 2           | Structure is clear, though checkmarks and meta chatter are less board-pack-like than the gold. |
| Source quality    | 1           | Source snippets are fixture-backed, but the run misses Calendar entirely and evidence metadata is weak. |
| **Total**         | **9/15**    |       |


**Top issue:** No Calendar tool use or calendar citation for Sales, which this case is explicitly designed to test.

---

## Case 02 — Xero Demo, February 2026

Run ID: `run_20260407_151341`
Date: 2026-04-07


| Dimension         | Score (0–3) | Notes |
| ----------------- | ----------- | ----- |
| Factual alignment | 1           | Core line-item figures match the CSV, but the Repairs body says 886% overspend while the header and CSV are about 786%. |
| Hallucination     | 3           | The campaign pull-forward, HVAC event, and lack of subscription context all come from the fixture rather than invented detail. |
| Coverage          | 2           | The three large movements are addressed and Sales stays below threshold, but the Repairs narrative omits the insurance-claim angle in the gold. |
| Tone & format     | 2           | Overall structure is solid and readable, if slightly conversational in places. |
| Source quality    | 2           | Sources are mostly fixture-aligned, but the case leaves some expected detail unused and Subscriptions has only an explicit no-context path. |
| **Total**         | **10/15**   |       |


**Top issue:** Repairs omits the insurance-claim detail from the fixture and includes an 886% vs 786% inconsistency.

---

## Case 03 — Xero Demo, January 2026

Run ID: `run_20260407_151409`
Date: 2026-04-07


| Dimension         | Score (0–3) | Notes |
| ----------------- | ----------- | ----- |
| Factual alignment | 2           | Sales numbers match the CSV, but the commentary does not fully reconcile the GBP 5,621 actual with all CRM detail available in the fixture. |
| Hallucination     | 2           | The named deals are fixture-backed, but the run overstates completeness without using the full narrow CRM evidence set. |
| Coverage          | 2           | Sales is covered and Subscriptions stays insignificant as intended, but the extra CRM-narrow detail is left on the table. |
| Tone & format     | 3           | The structure and register are strong and close to the intended finance-summary style. |
| Source quality    | 2           | Slack, Gmail, Calendar, and CRM appear, but the most useful CRM-narrow evidence is not actually used in the explanation. |
| **Total**         | **11/15**   |       |


**Top issue:** The run omits the CRM-narrow deals that explain the full GBP 5,621 actual, so the sales story is incomplete.

---

## Case 04 — Synthetic, Headcount

Run ID: `run_20260407_150837`
Date: 2026-04-07


| Dimension         | Score (0–3) | Notes |
| ----------------- | ----------- | ----- |
| Factual alignment | 2           | Per-line numbers match the CSV, but some timing and roll-up phrasing are looser than the fixture and gold. |
| Hallucination     | 2           | The six stories are largely grounded in Slack and Gmail, though some phrasing is more agent-meta than ideal. |
| Coverage          | 2           | All six significant lines and the two insignificant lines are handled, but the expected CRM linkage for contractor spend is missing. |
| Tone & format     | 2           | Structure is good, though it includes some awkward meta language and malformed trailing `**` in headers. |
| Source quality    | 1           | The prose aligns with the fixture, but the structured sources are effectively broken and CRM evidence is not surfaced. |
| **Total**         | **9/15**    |       |


**Top issue:** Contractor spend should explicitly tie to CRM project `PLAT-001` and the approved USD 50k envelope, not only Slack and Gmail.

---

## Case 05 — Synthetic, Marketing Campaign Timing

Run ID: `run_20260407_150105`
Date: 2026-04-07


| Dimension         | Score (0–3) | Notes |
| ----------------- | ----------- | ----- |
| Factual alignment | 1           | Significant line numbers match, but the executive summary presents sub-line totals as if they were full department totals, which contradicts the CSV. |
| Hallucination     | 2           | The digital, events, and creative narratives are fixture-backed, but the top-line framing is materially misleading. |
| Coverage          | 2           | All significant and insignificant lines are addressed, though some gold-level detail about quarter timing and event mix is missing. |
| Tone & format     | 1           | The use of emoji markers makes the output feel less like a clean board-pack summary. |
| Source quality    | 2           | Sources broadly match the fixture, but provenance fields are noisy and not especially machine-clean. |
| **Total**         | **8/15**    |       |


**Top issue:** The executive summary states sub-line totals as if they were the full February marketing budget and actual.

---

## Case 06 — Synthetic, Professional Fees Spike

Run ID: `run_20260407_151444`
Date: 2026-04-07


| Dimension         | Score (0–3) | Notes |
| ----------------- | ----------- | ----- |
| Factual alignment | 2           | Core budget and actual figures match, but the forward-looking residual IP cost does not line up with the narrow fixture and gold. |
| Hallucination     | 2           | The main legal and audit stories are grounded, but the forecast tail on remaining IP work stretches beyond the strongest evidence. |
| Coverage          | 2           | Both significant lines and the insignificant rows are present, though the run misses some gold specifics such as Vantec and the Q1 residual range. |
| Tone & format     | 3           | This is one of the cleaner runs structurally and reads like a professional FP&A note. |
| Source quality    | 2           | Source use is solid, but some amount and timing details are not the best-supported version available in the fixture. |
| **Total**         | **11/15**   |       |


**Top issue:** The remaining IP-cost timing and magnitude drift from the narrow fixture and the gold commentary.

---

## Case 07 — Synthetic, Revenue Miss

Run ID: `run_20260407_150923`
Date: 2026-04-07


| Dimension         | Score (0–3) | Notes |
| ----------------- | ----------- | ----- |
| Factual alignment | 1           | Revenue and Professional Services are directionally right, but Cost of Revenue is treated as unexplained even though the fixture explains it. |
| Hallucination     | 2           | Most deal detail is traceable to CRM and Slack, but the strong no-context framing for COR contradicts available evidence. |
| Coverage          | 1           | COR is materially mishandled and Professional Services leaves useful CRM-backed detail unused. |
| Tone & format     | 2           | The structure is mostly acceptable, but malformed headers and over-hedged COR language weaken the output. |
| Source quality    | 1           | Revenue sourcing is decent, but COR relies on placeholder no-evidence style sourcing despite CRM being the primary source for the case. |
| **Total**         | **7/15**    |       |


**Top issue:** Cost of Revenue is framed as unexplained even though the CRM fixtures provide a direct onboarding-and-slippage explanation.

---

## Summary


| Case        | Total   | Top Issue |
| ----------- | ------- | --------- |
| Case 01     | 9/15    | Missing Calendar evidence on Sales |
| Case 02     | 10/15   | Repairs inconsistency and missing insurance-claim angle |
| Case 03     | 11/15   | Sales story omits key CRM-narrow detail |
| Case 04     | 9/15    | Contractor spend misses CRM project linkage |
| Case 05     | 8/15    | Executive summary uses sub-line totals as full totals |
| Case 06     | 11/15   | Remaining IP-cost tail is not well grounded |
| Case 07     | 7/15    | Cost of Revenue ignores available CRM explanation |
| **Average** | **9.3/15** |           |


## Top 2–3 Recurring Failures

1. The model often leaves high-value fixture evidence unused, especially narrow CRM or Calendar evidence that the case was designed to exercise.
2. Executive summaries and forward-looking phrasing sometimes overstate confidence or mis-state totals even when line-item math is otherwise correct.
3. Source handling is inconsistent: some runs omit expected evidence, produce weak structured provenance, or fall back to no-context despite available fixture support.

## Next Fixes

- [ ] Force better use of narrow follow-up evidence when broad results do not fully reconcile the line-item story.
- [ ] Tighten prompt and validation around executive-summary totals so scoped line sums are not presented as full departmental totals.
- [ ] Improve source extraction and run-level validation so missing Calendar/CRM evidence and broken structured sources are surfaced earlier.

