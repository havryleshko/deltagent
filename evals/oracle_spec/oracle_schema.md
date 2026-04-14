# Oracle Schema

Use one oracle file per workbook, for example:

- `evals/oracles/aurora_hospitality_holdings_november_2024.json`

Each oracle should define workbook metadata, summary expectations, and line-level truth.

## Required workbook fields

```json
{
  "workbook": "aurora_hospitality_holdings_november_2024.xlsx",
  "period": "November 2024",
  "summary_expectations": {},
  "lines": []
}
```

## `summary_expectations`

Use this section to encode what a good opening summary must do.

```json
{
  "must_surface_lines": [
    "Property Rent — Managed",
    "Charitable & Community",
    "Property Insurance"
  ],
  "max_opening_drivers": 5,
  "forbid_mixed_total_story": true
}
```

Field semantics:

- `must_surface_lines`: material lines that should appear in the opening summary
- `max_opening_drivers`: upper bound to enforce brevity
- `forbid_mixed_total_story`: block the "single combined total across revenue and expense" pattern when it would be misleading

## `lines[]`

Each line item should include financial truth plus support expectations.

### Supported line

```json
{
  "line_item": "Food & Beverage Revenue",
  "budget_usd": 45400,
  "actual_usd": 50800,
  "variance_usd": 5400,
  "variance_pct": 11.9,
  "significant": true,
  "supported": true,
  "expected_driver": "higher-than-budgeted F&B volume from event/catering activity",
  "expected_driver_keywords": ["event", "catering", "volume", "outlet activity"],
  "allowed_source_families": ["slack", "gmail", "calendar", "crm"],
  "expected_evidence_ids": ["slack-aurora-017", "gmail-aurora-004"],
  "forward_risk": "may not recur if event activity was one-off",
  "mitigation_or_action": "confirm whether uplift was recurring or timing-related"
}
```

### Unsupported line

```json
{
  "line_item": "Property Insurance",
  "budget_usd": 143800,
  "actual_usd": 159200,
  "variance_usd": 15400,
  "variance_pct": 10.7,
  "significant": true,
  "supported": false
}
```

## Field guidance

- `supported`: whether planted evidence exists for this line
- `expected_driver`: canonical driver statement for scoring
- `expected_driver_keywords`: fallback matcher only; do not use this alone if stronger evidence matching is available
- `allowed_source_families`: source families that may legitimately support the line
- `expected_evidence_ids`: planted evidence records that should count as true support
- `forward_risk`: optional forward-looking implication expected in strong commentary
- `mitigation_or_action`: optional management action expected in strong commentary

## Evidence registry

Keep planted evidence in a separate registry so the oracle does not need to duplicate raw snippets.

```json
{
  "evidence": [
    {
      "id": "gmail-aurora-004",
      "source_family": "gmail",
      "line_item": "Food & Beverage Revenue",
      "date": "2024-11-08",
      "snippet": "Banquet client increased headcount; catering package expanded",
      "driver_tags": ["event", "catering", "volume"]
    }
  ]
}
```

## Scoring notes

- A source section with `No evidence found`, `N/A`, or empty results is not evidence.
- A line with `supported: false` should not receive credit for specific causal claims.
- Generic hypotheses may be tolerated only when clearly labeled as uncertain and not presented as fact.
