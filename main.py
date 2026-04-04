from __future__ import annotations

import sys

from ui.app import run_tui


def main() -> int:
    csv_path = sys.argv[1] if len(sys.argv) > 1 else None
    run_tui(initial_csv_path=csv_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
