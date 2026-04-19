from __future__ import annotations

import json
from pathlib import Path

from evals.round2.build_round2_eval_bundles import build_specs, write_bundle

from evals.round4.round4_bundle_specs import round4_extra_specs


def build_round4_specs() -> list[dict]:
    all_built = build_specs()
    if len(all_built) < 11:
        raise RuntimeError("build_specs() must include index 10 (lumen) for round 4")
    return [all_built[10]] + round4_extra_specs()


def main() -> None:
    root = Path(__file__).resolve().parent
    root.mkdir(parents=True, exist_ok=True)
    specs = build_round4_specs()
    if len(specs) != 10:
        raise RuntimeError(f"round 4 expects 10 bundles, got {len(specs)}")
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
