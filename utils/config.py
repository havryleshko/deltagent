from __future__ import annotations

import os
from dataclasses import dataclass

_DEFAULT_PCT = 10.0
_DEFAULT_ABS = 1000.0
_DEFAULT_CURRENCY = "$"


def _parse_float_env(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or not str(raw).strip():
        return default
    try:
        return float(str(raw).strip())
    except ValueError:
        return default


def _parse_currency_symbol() -> str:
    raw = os.environ.get("DELTAGENT_CURRENCY_SYMBOL")
    if raw is None or not str(raw).strip():
        return _DEFAULT_CURRENCY
    return str(raw).strip()


@dataclass(frozen=True)
class DeltagentConfig:
    significance_pct_threshold: float
    significance_abs_variance_threshold: float
    currency_symbol: str


def load_config() -> DeltagentConfig:
    return DeltagentConfig(
        significance_pct_threshold=_parse_float_env(
            "DELTAGENT_SIGNIFICANCE_PCT", _DEFAULT_PCT
        ),
        significance_abs_variance_threshold=_parse_float_env(
            "DELTAGENT_SIGNIFICANCE_ABS", _DEFAULT_ABS
        ),
        currency_symbol=_parse_currency_symbol(),
    )
