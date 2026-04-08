# Phase B Eval Scorecard — Rerun

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

Run ID: `run_20260408_101219`
Date: 2026-04-08

| Dimension         | Score (0–3) | Notes                                                                                                                           |
| ----------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Factual alignment | 3           | Sales and Purchases now reconcile cleanly to the Meridian pull-forward and linked deployment cost.                             |
| Hallucination     | 3           | All commercial detail is fixture-backed and no unsupported narrative is introduced.                                            |
| Coverage          | 3           | Both significant lines are handled well and the Purchases linkage is explicit.                                                 |
| Tone & format     | 2           | The final structure is acceptable, but the run still includes meta-preface language and reads longer than the gold.            |
| Source quality    | 2           | Calendar use is fixed, but Sales still leans on CRM plus Calendar rather than the fuller multi-tool evidence profile available. |
| **Total**         | **13/15**   |                                                                                                                                 |

**Top issue:** Calendar evidence is now present, but the Sales explanation still does not use the full evidence richness available in the fixture.

---

## Case 02 — Xero Demo, February 2026

Run ID: `run_20260408_101324`
Date: 2026-04-08

| Dimension         | Score (0–3) | Notes                                                                                                                                   |
| ----------------- | ----------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| Factual alignment | 2           | Core numbers are correct and the 786.3% Repairs inconsistency is fixed, but the run still misses the insurance-claim angle in Repairs. |
| Hallucination     | 3           | The campaign, HVAC event, and Subscription uncertainty stay anchored to fixture evidence or explicit lack of evidence.                  |
| Coverage          | 2           | All significant lines are addressed, but Subscriptions still relies on a weak no-context treatment and Repairs leaves useful detail out. |
| Tone & format     | 2           | The structure is usable, though the prose is still verbose and slightly operational.                                                    |
| Source quality    | 1           | The Subscription no-evidence block is rendered as malformed source rows, which the parser correctly flags.                             |
| **Total**         | **10/15**   |                                                                                                                                         |

**Top issue:** The Repairs narrative is better numerically, but Subscriptions still emits malformed placeholder source rows and Repairs still omits the insurance-claim detail.

---

## Case 03 — Xero Demo, January 2026

Run ID: `run_20260408_101352`
Date: 2026-04-08

| Dimension         | Score (0–3) | Notes                                                                                                                                   |
| ----------------- | ----------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| Factual alignment | 2           | The main Sales story is right, but the residual gap between CRM carry-over totals and booked actual remains only partially reconciled.  |
| Hallucination     | 3           | The deal names, timing, and CFO approval are grounded in the fixture.                                                                   |
| Coverage          | 3           | The single significant line is covered well and the zero-budget noise is kept out of scope.                                             |
| Tone & format     | 2           | The register is broadly fine, but it still opens with meta commentary and runs longer than needed.                                      |
| Source quality    | 1           | The evidence itself is good, but the final source rows are malformed and therefore fail the structured provenance requirement.           |
| **Total**         | **11/15**   |                                                                                                                                         |

**Top issue:** The commercial story is much better, but malformed source formatting drags down an otherwise solid run.

---

## Case 04 — Synthetic, Headcount

Run ID: `run_20260408_101521`
Date: 2026-04-08

| Dimension         | Score (0–3) | Notes                                                                                                                                 |
| ----------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Factual alignment | 3           | The six significant lines reconcile well, including the previously missing contractor bridge.                                        |
| Hallucination     | 3           | Each explanation is supported by fixture evidence and the contractor story now correctly ties to `PLAT-001`.                         |
| Coverage          | 3           | All six significant lines and the two insignificant lines are handled correctly.                                                     |
| Tone & format     | 2           | This is materially cleaner than the baseline, though still more operational and action-heavy than the gold board-pack style.         |
| Source quality    | 2           | Contractor sourcing is much stronger, but several salary lines still rely on a single-source explanation rather than richer support. |
| **Total**         | **13/15**   |                                                                                                                                      |

**Top issue:** Contractor linkage is fixed, but several salary lines still rest on thin single-source evidence.

---

## Case 05 — Synthetic, Marketing Campaign Timing

Run ID: `run_20260408_101608`
Date: 2026-04-08

| Dimension         | Score (0–3) | Notes                                                                                                                              |
| ----------------- | ----------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| Factual alignment | 3           | The executive summary now uses the correct scoped totals for the marketing department and the line-item math is clean.            |
| Hallucination     | 3           | The timing explanations, venue credit, and billing timing all track directly to the fixture.                                      |
| Coverage          | 3           | All significant and insignificant lines are handled properly, and the period-shift logic is explicit.                             |
| Tone & format     | 2           | The output is strong, but still somewhat long and action-heavy relative to the gold.                                              |
| Source quality    | 3           | Source selection is strong across Slack, Gmail, and Calendar and aligns well with the evidence profile for the case.              |
| **Total**         | **14/15**   |                                                                                                                                  |

**Top issue:** The summary-scope bug is fixed; the remaining gap is mostly stylistic concision rather than correctness.

---

## Case 06 — Synthetic, Professional Fees Spike

Run ID: `run_20260408_101641`
Date: 2026-04-08

| Dimension         | Score (0–3) | Notes                                                                                                                                      |
| ----------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Factual alignment | 2           | The main invoice logic is correct, but the forward-looking residual exposure is still less precise than the gold commentary.               |
| Hallucination     | 2           | The core story is grounded, but the reserve-style forward estimate stretches beyond the strongest evidence in the fixture.                 |
| Coverage          | 2           | Both significant lines are addressed, though some gold-level specifics remain unused.                                                      |
| Tone & format     | 3           | Structurally this remains one of the cleaner reports.                                                                                      |
| Source quality    | 1           | The evidence is fixture-backed, but the final source rows are malformed and lose structured provenance.                                    |
| **Total**         | **10/15**   |                                                                                                                                            |

**Top issue:** The narrative is directionally right, but malformed source blocks and a still-loose forward exposure estimate cap the score.

---

## Case 07 — Synthetic, Revenue Miss

Run ID: `run_20260408_101731`
Date: 2026-04-08

| Dimension         | Score (0–3) | Notes                                                                                                                                      |
| ----------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Factual alignment | 2           | The COR and Professional Services linkage is now materially better, but some timing language still overstates November recovery certainty. |
| Hallucination     | 3           | The deal, PS, and COR explanations are grounded in CRM and Slack rather than invented evidence.                                            |
| Coverage          | 3           | The previously mishandled Cost of Revenue line is now clearly explained as a downstream onboarding effect.                                 |
| Tone & format     | 1           | The structure is workable, but the prose is still long and the malformed source formatting hurts presentation quality.                     |
| Source quality    | 1           | The source evidence is much better chosen, but the final source rows are malformed across all three significant lines.                     |
| **Total**         | **10/15**   |                                                                                                                                            |

**Top issue:** The core commercial logic is fixed, but source formatting and some overconfident recovery phrasing still hold the run back.

---

## Summary

| Case        | Old Total | New Total | Delta | Top Issue                                                        |
| ----------- | --------- | --------- | ----- | ---------------------------------------------------------------- |
| Case 01     | 9/15      | 13/15     | +4    | Sales still does not use the full evidence richness available    |
| Case 02     | 10/15     | 10/15     | +0    | Malformed no-evidence sources and missing insurance-claim detail |
| Case 03     | 11/15     | 11/15     | +0    | Source formatting is malformed                                   |
| Case 04     | 9/15      | 13/15     | +4    | Some salary lines still rely on thin evidence                    |
| Case 05     | 8/15      | 14/15     | +6    | Mostly stylistic concision remains                               |
| Case 06     | 11/15     | 10/15     | -1    | Source formatting regressed; residual exposure still loose       |
| Case 07     | 7/15      | 10/15     | +3    | Source formatting and recovery certainty still too weak          |
| **Average** | **9.3/15**| **11.6/15**| **+2.3** |                                                              |

## Comparison

The rerun improves the measured average from `9.3/15` to `11.6/15`, which lands inside the expected `10.8–11.8/15` target range for this fix round.

The biggest gains come from the intended areas:
- Case 01 now uses Calendar evidence and links Purchases to the pulled-forward deal.
- Case 04 now surfaces the missing contractor CRM linkage and reconciles the full contractor bridge.
- Case 05 no longer presents significant-line totals as if they were the full departmental totals.
- Case 07 now explains Professional Services and Cost of Revenue as downstream consequences of the same commercial slips.

The largest remaining drag is now source rendering, not evidence retrieval:
- Cases 02, 03, 06, and 07 still emit malformed source rows in the final text, so the parser correctly downgrades source quality.
- Some runs still overstate confidence on forward timing or residual exposure even when the core variance story is directionally correct.
- Case 02 still leaves useful Repairs detail on the table, and Case 06 still does not match the gold's tighter forward-exposure framing.

## Top 2–3 Recurring Failures

1. Source formatting remains inconsistent in final model output, especially when the model uses em dashes or placeholder no-evidence rows instead of the strict structured format.
2. Some executive summaries and line commentaries still overstate certainty on forward timing or residual exposure after the core variance is already explained.
3. A few cases still leave gold-level evidence unused even when the primary story is now correct.
