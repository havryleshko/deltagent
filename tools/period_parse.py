from __future__ import annotations

import calendar
from datetime import datetime, timezone
from typing import Tuple


def parse_period_to_utc_range(period: str) -> Tuple[str, str] | None:
    raw = (period or "").strip()
    if not raw:
        return None
    start_naive: datetime | None = None
    for fmt in ("%B %Y", "%b %Y"):
        try:
            start_naive = datetime.strptime(raw, fmt)
            break
        except ValueError:
            continue
    if start_naive is None:
        return None
    year, month = start_naive.year, start_naive.month
    last = calendar.monthrange(year, month)[1]
    start = datetime(year, month, 1, 0, 0, 0, tzinfo=timezone.utc)
    end = datetime(year, month, last, 23, 59, 59, tzinfo=timezone.utc)
    return (
        start.isoformat().replace("+00:00", "Z"),
        end.isoformat().replace("+00:00", "Z"),
    )
