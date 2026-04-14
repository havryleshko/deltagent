from __future__ import annotations

import pytest

from agent.prompts import build_user_message
from tests.test_phase1_agent_core import FIXTURE_CSV
from utils.config import load_config
from utils.csv_validator import validate_csv


def test_build_user_message_currency_symbol_gbp():
    significant, insignificant, _ = validate_csv(FIXTURE_CSV)
    text = build_user_message(significant, insignificant, currency_symbol="£")
    assert "£" in text
    assert "$" not in text
    assert "Full report totals" not in text
    assert "Significant-line totals:" in text


def test_validate_csv_high_thresholds_all_insignificant():
    significant, insignificant, errors = validate_csv(
        FIXTURE_CSV,
        significance_pct_threshold=99.0,
        significance_abs_variance_threshold=1e12,
    )
    assert not errors
    assert not significant
    assert len(insignificant) >= 1


def test_load_config_invalid_env_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DELTAGENT_SIGNIFICANCE_PCT", "not_a_number")
    monkeypatch.setenv("DELTAGENT_SIGNIFICANCE_ABS", "also_bad")
    monkeypatch.setenv("DELTAGENT_CURRENCY_SYMBOL", "")
    cfg = load_config()
    assert cfg.significance_pct_threshold == 10.0
    assert cfg.significance_abs_variance_threshold == 1000.0
    assert cfg.currency_symbol == "$"


def test_load_config_custom_currency(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DELTAGENT_CURRENCY_SYMBOL", "€")
    cfg = load_config()
    assert cfg.currency_symbol == "€"
