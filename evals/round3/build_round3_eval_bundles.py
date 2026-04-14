from __future__ import annotations

import json
from pathlib import Path

from evals.round2.build_round2_eval_bundles import build_specs, write_bundle


def main() -> None:
    root = Path(__file__).resolve().parent
    root.mkdir(parents=True, exist_ok=True)
    specs = build_specs()[:10]
    for spec in specs:
        write_bundle(root, spec)
    manifest = {
        "period": "November 2024",
        "bundle_count": len(specs),
        "bundles": [
            {
                "slug": spec["slug"],
                "xlsx": f"{spec['slug']}.xlsx",
                "mock_context": f"{spec['slug']}.mock_context.json",
                "oracle": f"{spec['slug']}.oracle.json",
            }
            for spec in specs
        ],
    }
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
