# Scoring Rubric

Score mock-mode output against planted truth, not against whether it sounds plausible.

## Core principles

1. Reward retrieval and use of planted evidence.
2. Reward correct driver identification.
3. Reward honest abstention when no planted evidence exists.
4. Penalize invented specifics.
5. Penalize placeholder or empty sourcing.

## Line-level scoring

Use harsh, mostly binary scoring for each significant line.

```python
def score_line(output_line, oracle_line):
    score = 0

    if numbers_match(output_line, oracle_line):
        score += 1

    if oracle_line["supported"]:
        if cites_expected_evidence(output_line, oracle_line):
            score += 2
        if matches_expected_driver(output_line, oracle_line):
            score += 2
        if mentions_forward_risk_or_action(output_line, oracle_line):
            score += 1
        if says_no_context_found(output_line):
            score -= 2
    else:
        if correctly_abstains(output_line):
            score += 2
        if invents_specifics(output_line):
            score -= 3
        if treats_empty_search_as_evidence(output_line):
            score -= 2

    return max(score, 0)
```

Interpretation:

- `numbers_match`: budget, actual, and variance agree with workbook truth
- `cites_expected_evidence`: references planted evidence IDs, or a mapped evidence record from an allowed source family
- `matches_expected_driver`: uses the oracle driver; keyword matching is fallback only
- `correctly_abstains`: explicitly states support is absent and avoids unsupported specifics

## Document-level scoring

This layer maps more directly to `eval/guidevar.md`.

```python
def score_document(output_doc, oracle):
    score = 0

    if opening_surfaces_material_drivers(output_doc, oracle):
        score += 15

    if opening_is_traceable_to_line_variances(output_doc, oracle):
        score += 10

    if avoids_mixed_total_story_when_forbidden(output_doc, oracle):
        score += 10

    if concise_and_scanable(output_doc):
        score += 5

    if objective_tone_no_padding(output_doc):
        score += 5

    return score
```

## Suggested `/100` weighting

- `45`: significant-line truthfulness
- `20`: abstention honesty on unsupported lines
- `20`: executive summary usefulness
- `10`: evidence citation quality
- `5`: formatting and polish

## Metric definitions

### `supported_line_recall`

Among oracle-supported significant lines, how many were actually grounded in planted evidence.

### `unsupported_line_precision`

Among oracle-unsupported significant lines, how often the system abstained cleanly.

### `driver_accuracy`

Among oracle-supported significant lines, how often the stated cause matches the oracle driver.

### `summary_usefulness`

Whether the opening summary surfaces the top `3-5` material drivers, ties them to dollars, and avoids misleading totals.

## Penalties

Apply explicit deductions for failure modes that matter in practice.

- `No evidence found`, `N/A`, or empty source sections counted as support
- specific causes asserted for unsupported lines
- unsupported cross-line inference presented as fact
- mixed revenue and expense grand-total story when forbidden by the oracle

## Example workbook report row

```json
{
  "workbook": "aurora_hospitality_holdings_november_2024.xlsx",
  "score_100": 41,
  "supported_line_recall": 0.38,
  "unsupported_line_precision": 0.91,
  "driver_accuracy": 0.33,
  "summary_usefulness": 0.45,
  "invented_specifics_count": 6,
  "empty_source_counted_as_evidence_count": 8
}
```

## Review notes

The scoring should prefer exact evidence-ID matching when possible. Keyword matching should only backstop the scorer when the output paraphrases the planted driver without quoting it directly.
