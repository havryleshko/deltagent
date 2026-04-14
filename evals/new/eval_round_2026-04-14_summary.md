# Eval Round 2026-04-14 (10 New XLSX)

Runs executed with `python -m cli run evals/new/<file>.xlsx` using inferred period labels.


| File                                               | Exit | Saved run                       | Gaps | Tool diagnostics (total/unique/dupes) | Sourced significant lines | Rollup check |
| -------------------------------------------------- | ---- | ------------------------------- | ---- | ------------------------------------- | ------------------------- | ------------ |
| `meridian_biopharma_labs_november_2024.xlsx`       | 0    | `runs/run_20260414_150815.json` | 12   | 27/27/0                               | 1/9                       | pass         |
| `cobalt_mining_equipment_november_2024.xlsx`       | 0    | `runs/run_20260414_150916.json` | 7    | 12/12/0                               | 0/4                       | pass         |
| `aurora_hospitality_holdings_november_2024.xlsx`   | 0    | `runs/run_20260414_151049.json` | 9    | 27/27/0                               | 8/8                       | pass         |
| `redwood_timber_millwork_november_2024.xlsx`       | 0    | `runs/run_20260414_151157.json` | 13   | 20/20/0                               | 0/10                      | pass         |
| `vertex_edtech_solutions_november_2024.xlsx`       | 0    | `runs/run_20260414_151331.json` | 19   | 38/38/0                               | 0/15                      | pass         |
| `cirrus_aviation_services_november_2024.xlsx`      | 0    | `runs/run_20260414_151510.json` | 15   | 31/31/0                               | 1/12                      | pass         |
| `granite_municipal_it_services_november_2024.xlsx` | 0    | `runs/run_20260414_151631.json` | 13   | 27/27/0                               | 0/9                       | pass         |
| `silverline_wealth_advisors_november_2024.xlsx`    | 0    | `runs/run_20260414_151829.json` | 17   | 33/33/0                               | 1/15                      | pass         |
| `tempest_ocean_freight_november_2024.xlsx`         | 0    | `runs/run_20260414_152009.json` | 19   | 36/36/0                               | 1/16                      | pass         |
| `helios_renewable_power_november_2024.xlsx`        | 0    | `runs/run_20260414_152122.json` | 10   | 15/15/0                               | 1/7                       | pass         |


## Cross-cutting findings

- All runs succeeded: 10/10.
- Rollup safety check: 10/10 pass, 0/10 risky (criterion: total-style budget+actual phrasing without `sum of all lines`, `mixed revenue and expense`, or `significant-line totals`).
- Average gaps per file: 13.4.
- Average sourced significant-line coverage: 14.7%.
- Top diagnostic families by count: `search_slack=99`, `search_gmail=98`, `search_calendar=28`, `search_crm=20`.
- Tool diagnostic dedupe is holding for final diagnostics payloads in these runs (`dupes=0` across all files), but many unique `line_item_not_found` diagnostics remain.

## Prioritized next fixes

1. Expand deterministic mock context coverage for high-frequency new line items to reduce `line_item_not_found` and improve sourced-line coverage.
2. Strengthen exec-summary guardrails from phrase checks to numeric all-line-sum matching to catch unlabeled consolidated totals more reliably.
3. Add targeted alias mappings for recurring domain-specific labels (energy, logistics, facilities, compliance) in mock lookup.

## Artifacts

- Run log: `evals/new/eval_round_2026-04-14.log`
- Run index: `evals/new/eval_round_2026-04-14_runs.tsv`
- This summary: `evals/new/eval_round_2026-04-14_summary.md`

