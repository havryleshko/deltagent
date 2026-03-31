from __future__ import annotations

import asyncio
import sys

from agent.agent import run_agent
from utils.csv_validator import validate_csv


async def _run(csv_path: str) -> int:
    significant_rows, insignificant_rows, errors = validate_csv(csv_path)
    if errors:
        for error in errors:
            print(error)
        if not significant_rows and not insignificant_rows:
            return 1
    output = await run_agent(
        significant_rows=significant_rows,
        insignificant_rows=insignificant_rows,
    )
    print(output)
    return 0


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python main.py <csv_path>")
        return 1
    csv_path = sys.argv[1]
    return asyncio.run(_run(csv_path))


if __name__ == "__main__":
    raise SystemExit(main())
