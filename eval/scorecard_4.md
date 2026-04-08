# Phase B Eval Scorecard — Round 4

Score each case on five dimensions (0–3 per dimension, 0 = fail, 1 = partial, 2 = good, 3 = excellent). Round 4 reruns use post–Scorecard 3 recurring-fixes behavior (trace key alignment, confidence pass, whitelist detail appenders, tone prompts, optional `**` stripping, length diagnostics).


| Dimension         | Description                                                           |
| ----------------- | --------------------------------------------------------------------- |
| Factual alignment | Numbers in commentary match the CSV exactly                           |
| Hallucination     | No invented evidence, people, deals, or events                        |
| Coverage          | All significant lines addressed, insignificant handled correctly      |
| Tone & format     | Board-pack register, correct structure, concise                       |
| Source quality    | Sources cited are from the fixture; quality matches evidence richness |


---

## Case 01 — Xero Demo, March 2026

Run ID: `run_20260408_145826`
Date: 2026-04-08


| Dimension         | Score (0–3) | Notes |
| ----------------- | ----------- | ----- |
| Factual alignment | TBD         | Rescore from `eval/case_01_xero_march_2026/outputs/run_20260408_145826.json` (`raw_text` / `tool_diagnostics`). |
| Hallucination     | TBD         |       |
| Coverage          | TBD         |       |
| Tone & format     | TBD         |       |
| Source quality    | TBD         |       |
| **Total**         | **TBD/15**  |       |


**Top issue:** (fill after review)

---

## Case 02 — Xero Demo, February 2026

Run ID: `run_20260408_145918`
Date: 2026-04-08


| Dimension         | Score (0–3) | Notes |
| ----------------- | ----------- | ----- |
| Factual alignment | TBD         | Rescore from `eval/case_02_xero_feb_2026/outputs/run_20260408_145918.json`. |
| Hallucination     | TBD         |       |
| Coverage          | TBD         |       |
| Tone & format     | TBD         |       |
| Source quality    | TBD         |       |
| **Total**         | **TBD/15**  |       |


**Top issue:** (fill after review)

---

## Case 03 — Xero Demo, January 2026

Run ID: `run_20260408_145947`
Date: 2026-04-08


| Dimension         | Score (0–3) | Notes |
| ----------------- | ----------- | ----- |
| Factual alignment | TBD         | Rescore from `eval/case_03_xero_jan_2026/outputs/run_20260408_145947.json`. |
| Hallucination     | TBD         |       |
| Coverage          | TBD         |       |
| Tone & format     | TBD         |       |
| Source quality    | TBD         |       |
| **Total**         | **TBD/15**  |       |


**Top issue:** (fill after review)

---

## Case 04 — Synthetic, Headcount

Run ID: `run_20260408_150100`
Date: 2026-04-08


| Dimension         | Score (0–3) | Notes |
| ----------------- | ----------- | ----- |
| Factual alignment | TBD         | Rescore from `eval/case_04_synth_headcount/outputs/run_20260408_150100.json`. |
| Hallucination     | TBD         |       |
| Coverage          | TBD         |       |
| Tone & format     | TBD         |       |
| Source quality    | TBD         |       |
| **Total**         | **TBD/15**  |       |


**Top issue:** (fill after review)

---

## Case 05 — Synthetic, Marketing Campaign Timing

Run ID: `run_20260408_150138`
Date: 2026-04-08


| Dimension         | Score (0–3) | Notes |
| ----------------- | ----------- | ----- |
| Factual alignment | TBD         | Rescore from `eval/case_05_synth_marketing/outputs/run_20260408_150138.json`. |
| Hallucination     | TBD         |       |
| Coverage          | TBD         |       |
| Tone & format     | TBD         |       |
| Source quality    | TBD         |       |
| **Total**         | **TBD/15**  |       |


**Top issue:** (fill after review)

---

## Case 06 — Synthetic, Professional Fees Spike

Run ID: `run_20260408_150217`
Date: 2026-04-08


| Dimension         | Score (0–3) | Notes |
| ----------------- | ----------- | ----- |
| Factual alignment | TBD         | Rescore from `eval/case_06_synth_prof_fees/outputs/run_20260408_150217.json`. |
| Hallucination     | TBD         |       |
| Coverage          | TBD         |       |
| Tone & format     | TBD         |       |
| Source quality    | TBD         |       |
| **Total**         | **TBD/15**  |       |


**Top issue:** (fill after review)

---

## Case 07 — Synthetic, Revenue Miss

Run ID: `run_20260408_150304`
Date: 2026-04-08


| Dimension         | Score (0–3) | Notes |
| ----------------- | ----------- | ----- |
| Factual alignment | TBD         | Rescore from `eval/case_07_synth_revenue_miss/outputs/run_20260408_150304.json`. |
| Hallucination     | TBD         |       |
| Coverage          | TBD         |       |
| Tone & format     | TBD         |       |
| Source quality    | TBD         |       |
| **Total**         | **TBD/15**  |       |


**Top issue:** (fill after review)

---

## Summary


| Case    | Round 3   | Round 4   | Delta Vs R3 | Top Issue (after rescore) |
| ------- | --------- | --------- | ----------- | ------------------------- |
| Case 01 | 13/15     | TBD       | TBD         |                           |
| Case 02 | 11/15     | TBD       | TBD         |                           |
| Case 03 | 13/15     | TBD       | TBD         |                           |
| Case 04 | 13/15     | TBD       | TBD         |                           |
| Case 05 | 14/15     | TBD       | TBD         |                           |
| Case 06 | 12/15     | TBD       | TBD         |                           |
| Case 07 | 12/15     | TBD       | TBD         |                           |
| **Avg** | **12.6/15** | **TBD** | **TBD**     |                           |


## Code changes this round (for reviewers)

- Tool traces are grouped by a punctuation-insensitive line-item key (alphanumeric tokens) so `Repairs & Maintenance` and `Repairs Maintenance` share evidence for enrichment and validation.
- Partial-evidence detection, softening regexes, and confidence validation patterns were expanded; executive summary softening uses merged trace text including per-line slices.
- Narrow whitelist appenders for `venue credit` and `uspto` when present in trace text but absent from commentary.
- Prompt rules for board-pack brevity, hedged certainty, concrete facts from tool summaries, and no body `**` emphasis.
- Post-process strips `**` from executive summary and line commentary before rebuild; optional length diagnostics on `tool_diagnostics`.
