# Mock Oracle Eval Spec

This folder defines how to score variance-commentary quality in mock mode.

The goal is not to approximate "real Slack" or "real CRM". The goal is to score whether the system is faithful to planted synthetic truth when evidence exists, and whether it stays honest when evidence does not exist.

This spec is aligned to `eval/guidevar.md`:

- reward fast, traceable "so what" summaries
- reward evidence-backed driver explanations
- reward forward risk or mitigation when supported by evidence
- penalize invented specifics and placeholder sourcing

Two hard rules:

1. Empty or no-result source blocks do not count as evidence.
2. Unsupported lines should earn credit for abstention, not for plausible-sounding guesses.

Recommended files in this folder:

- `oracle_schema.md`: expected oracle fields and semantics
- `scoring_rubric.md`: scoring weights, penalties, and metrics
- `example_oracle.json`: concrete workbook-level oracle example

Recommended top-line metrics:

- `supported_line_recall`
- `unsupported_line_precision`
- `driver_accuracy`
- `summary_usefulness`
- `score_100`

Recommended interpretation:

- low `supported_line_recall` means the system is not using planted truth
- low `unsupported_line_precision` means the system is hallucinating
- low `summary_usefulness` means the output may be safe but still weak for leadership use
