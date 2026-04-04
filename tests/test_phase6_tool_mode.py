from __future__ import annotations

import pytest

from tools import build_mock_tool_registry, build_tool_registry
from tools.gmail_tool import search_gmail
from tools.period_parse import parse_period_to_utc_range
from tools.tool_mode import is_live_tool_mode


def test_parse_period_november_2024():
    r = parse_period_to_utc_range("November 2024")
    assert r is not None
    assert r[0].startswith("2024-11-01")
    assert r[1].startswith("2024-11-30")


def test_parse_period_invalid_returns_none():
    assert parse_period_to_utc_range("") is None
    assert parse_period_to_utc_range("not a month") is None


def test_build_tool_registry_matches_mock_keys():
    assert set(build_tool_registry().keys()) == set(build_mock_tool_registry().keys())


@pytest.mark.asyncio
async def test_live_gmail_missing_client_file_returns_string(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    monkeypatch.setenv("DELTAGENT_TOOL_MODE", "live")
    monkeypatch.setenv("GOOGLE_CREDENTIALS_PATH", str(tmp_path / "nope.json"))
    out = await search_gmail(
        {
            "period": "November 2024",
            "line_item": "Revenue",
            "query": "test",
        }
    )
    assert "OAuth client JSON not found" in out or "Missing OAuth" in out


@pytest.mark.asyncio
async def test_mock_mode_uses_fixture_gmail(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DELTAGENT_TOOL_MODE", "mock")
    assert not is_live_tool_mode()
    out = await search_gmail(
        {
            "period": "November 2024",
            "line_item": "Professional Fees",
            "query": "x",
        }
    )
    assert "invoice" in out.lower() or "approval" in out.lower() or "Professional" in out
