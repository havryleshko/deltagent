# Round 2 Post-fix Baseline

- Seeded workbooks: `10`
- Average score: `60.92/100`

## Worst performers

- `forge_industrial_components_november_2024.xlsx`: `43.13/100`
- `harborline_health_clinics_november_2024.xlsx`: `45.62/100`
- `keystone_field_operations_november_2024.xlsx`: `53.12/100`

## Per-workbook breakdown

## bluebird_biotech_services_november_2024.xlsx

- Score: `89.17/100`
- Supported recall: `1.00`
- Unsupported precision: `1.00`
- Driver accuracy: `1.00`
- Summary usefulness: `0.83`
- Breakdown: truthfulness `37.5`, abstention `20.0`, summary `16.67`, evidence `10.0`, polish `5.0`

## cedar_facilities_management_november_2024.xlsx

- Score: `59.58/100`
- Supported recall: `0.33`
- Unsupported precision: `1.00`
- Driver accuracy: `0.33`
- Summary usefulness: `0.83`
- Breakdown: truthfulness `15.0`, abstention `20.0`, summary `16.67`, evidence `3.33`, polish `4.58`

## delta_logistics_network_november_2024.xlsx

- Score: `73.34/100`
- Supported recall: `0.67`
- Unsupported precision: `1.00`
- Driver accuracy: `0.67`
- Summary usefulness: `0.83`
- Breakdown: truthfulness `25.0`, abstention `20.0`, summary `16.67`, evidence `6.67`, polish `5.0`

## ember_saas_security_november_2024.xlsx

- Score: `60.2/100`
- Supported recall: `0.75`
- Unsupported precision: `0.00`
- Driver accuracy: `0.75`
- Summary usefulness: `1.00`
- Breakdown: truthfulness `28.12`, abstention `0.0`, summary `20.0`, evidence `7.5`, polish `4.58`

## forge_industrial_components_november_2024.xlsx

- Score: `43.13/100`
- Supported recall: `0.50`
- Unsupported precision: `0.00`
- Driver accuracy: `0.25`
- Summary usefulness: `0.83`
- Breakdown: truthfulness `16.88`, abstention `0.0`, summary `16.67`, evidence `5.0`, polish `4.58`

## glenhaven_hospitality_group_november_2024.xlsx

- Score: `55.21/100`
- Supported recall: `0.75`
- Unsupported precision: `0.00`
- Driver accuracy: `0.50`
- Summary usefulness: `0.92`
- Breakdown: truthfulness `24.38`, abstention `0.0`, summary `18.33`, evidence `7.5`, polish `5.0`

## harborline_health_clinics_november_2024.xlsx

- Score: `45.62/100`
- Supported recall: `0.50`
- Unsupported precision: `0.00`
- Driver accuracy: `0.50`
- Summary usefulness: `0.75`
- Breakdown: truthfulness `20.62`, abstention `0.0`, summary `15.0`, evidence `5.0`, polish `5.0`

## iona_renewable_storage_november_2024.xlsx

- Score: `57.29/100`
- Supported recall: `0.75`
- Unsupported precision: `0.00`
- Driver accuracy: `0.75`
- Summary usefulness: `0.83`
- Breakdown: truthfulness `28.12`, abstention `0.0`, summary `16.67`, evidence `7.5`, polish `5.0`

## juniper_retail_media_november_2024.xlsx

- Score: `72.5/100`
- Supported recall: `1.00`
- Unsupported precision: `0.00`
- Driver accuracy: `1.00`
- Summary usefulness: `1.00`
- Breakdown: truthfulness `37.5`, abstention `0.0`, summary `20.0`, evidence `10.0`, polish `5.0`

## keystone_field_operations_november_2024.xlsx

- Score: `53.12/100`
- Supported recall: `0.75`
- Unsupported precision: `0.00`
- Driver accuracy: `0.25`
- Summary usefulness: `1.00`
- Breakdown: truthfulness `20.62`, abstention `0.0`, summary `20.0`, evidence `7.5`, polish `5.0`

## Suggested next steps

1. Fix unsupported-line abstention reliability (highest leverage): in `7/10` bundles, unsupported precision remains `0.00`, which means unsupported lines still include speculative content instead of clean abstention.
2. Raise supported-line truthfulness on the weakest books first:

- `forge_industrial_components_november_2024.xlsx` (`43.13`) and `harborline_health_clinics_november_2024.xlsx` (`45.62`) should be used as primary debug cases.
- focus on driver matching and amount/period correctness before stylistic polish.

1. Improve driver accuracy floor:

- `keystone_field_operations_november_2024.xlsx` driver accuracy is `0.25`.
- `forge_industrial_components_november_2024.xlsx` driver accuracy is `0.25`.
- goal for next pass: bring all bundles to `>=0.50` driver accuracy.

1. Keep summary behavior stable while fixing line-level logic:

- summary usefulness is already strong (`0.75-1.00` in post-fix).
- avoid regressing summary quality while tightening abstention and driver grounding.

1. Define next acceptance gate for Round 3:

- average score `>=70`.
- unsupported precision non-zero in every bundle, with at least `7/10` bundles `>=0.80`.
- no bundle below `55`.

