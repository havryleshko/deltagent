from __future__ import annotations

from pathlib import Path

from evals.oracle_scorer import render_markdown_report, score_oracle_dir


def main() -> None:
    root = Path(__file__).resolve().parent
    results = score_oracle_dir(root / "oracles")
    report = render_markdown_report(results)
    output_path = root / "baseline_round1.md"
    output_path.write_text(report + "\n", encoding="utf-8")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
