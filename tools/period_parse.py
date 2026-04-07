from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class PeriodWindow:
    label: str
    start_iso: str
    end_iso: str


def resolve_period(period: str) -> PeriodWindow | None:
    raw = (period or "").strip()
    if not raw:
        return None
    start_naive: datetime | None = None
    display_label = raw
    for fmt in ("%Y-%m", "%B %Y", "%b %Y"):
        try:
            start_naive = datetime.strptime(raw, fmt)
            if fmt == "%Y-%m":
                display_label = start_naive.strftime("%B %Y")
            else:
                display_label = start_naive.strftime("%B %Y")
            break
        except ValueError:
            continue
    if start_naive is None:
        return None
    year, month = start_naive.year, start_naive.month
    last = calendar.monthrange(year, month)[1]
    start = datetime(year, month, 1, 0, 0, 0, tzinfo=timezone.utc)
    end = datetime(year, month, last, 23, 59, 59, tzinfo=timezone.utc)
    return PeriodWindow(
        label=display_label,
        start_iso=start.isoformat().replace("+00:00", "Z"),
        end_iso=end.isoformat().replace("+00:00", "Z"),
    )


def parse_period_to_utc_range(period: str) -> tuple[str, str] | None:
    window = resolve_period(period)
    if window is None:
        return None
    return window.start_iso, window.end_iso
