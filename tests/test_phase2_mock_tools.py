from __future__ import annotations

import asyncio
import time
from pathlib import Path

import pytest

from agent.agent import run_agent
from tools import build_mock_tool_registry
from tools.definitions import TOOL_DEFINITIONS
from tools.mock_data import FIXTURE_PATH, load_context
from utils.csv_validator import validate_csv

FIXTURE_CSV = Path(__file__).parent / "fixtures" / "sample_november_2024.csv"


class FakeMessages:
    def __init__(self, responses: list[object]) -> None:
        self._responses = responses
        self.calls: list[dict] = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        return self._responses.pop(0)


class FakeClient:
    def __init__(self, responses: list[object]) -> None:
        self.messages = FakeMessages(responses)


class FakeResponse:
    def __init__(self, stop_reason: str, content: list[dict]) -> None:
        self.stop_reason = stop_reason
        self.content = content


def test_tool_definitions_have_exclusions():
    names = {item["name"] for item in TOOL_DEFINITIONS}
    assert names == {"search_slack", "search_gmail", "search_calendar", "search_crm"}
    for definition in TOOL_DEFINITIONS:
        assert "Does NOT find" in definition["description"]


def test_canonical_fixture_is_single_period_and_shared():
    context = load_context()
    assert FIXTURE_PATH.name == "mock_context_november_2024.json"
    assert context["period"] == "November 2024"
    assert set(context["tool_responses"].keys()) == {
        "search_slack",
        "search_gmail",
        "search_calendar",
        "search_crm",
    }
    assert "Revenue" in context["tool_responses"]["search_crm"]
    assert "Professional Fees" in context["tool_responses"]["search_slack"]
    assert "Professional Fees" in context["tool_responses"]["search_gmail"]
    assert "Professional Fees" in context["tool_responses"]["search_calendar"]


@pytest.mark.asyncio
async def test_mock_tools_return_strings_and_do_not_raise():
    tools = build_mock_tool_registry()
    payload = {"period": "November 2024", "line_item": "Professional Fees"}
    for handler in tools.values():
        value = await handler(payload)
        assert isinstance(value, str)
    error_value = await tools["search_slack"]({"period": "November 2024"})
    assert "Tool error (search_slack)" in error_value


@pytest.mark.asyncio
async def test_run_agent_supports_multiple_tool_rounds_without_loop_rewrite():
    significant, insignificant, _ = validate_csv(FIXTURE_CSV)
    responses = [
        FakeResponse(
            stop_reason="tool_use",
            content=[
                {
                    "type": "tool_use",
                    "id": "toolu_1",
                    "name": "search_slack",
                    "input": {"period": "November 2024", "line_item": "Salaries"},
                },
                {
                    "type": "tool_use",
                    "id": "toolu_2",
                    "name": "search_gmail",
                    "input": {"period": "November 2024", "line_item": "Salaries"},
                },
            ],
        ),
        FakeResponse(
            stop_reason="tool_use",
            content=[
                {
                    "type": "tool_use",
                    "id": "toolu_3",
                    "name": "search_calendar",
                    "input": {"period": "November 2024", "line_item": "Salaries"},
                }
            ],
        ),
        FakeResponse(
            stop_reason="end_turn",
            content=[
                {
                    "type": "text",
                    "text": "EXECUTIVE SUMMARY\nok\nLINE COMMENTARY\nok\nINSIGNIFICANT VARIANCES\nok",
                }
            ],
        ),
    ]
    client = FakeClient(responses)
    output = await run_agent(
        significant_rows=significant,
        insignificant_rows=insignificant,
        client=client,
        tool_registry=build_mock_tool_registry(),
    )
    assert "EXECUTIVE SUMMARY" in output
    assert len(client.messages.calls) == 3


@pytest.mark.asyncio
async def test_parallel_multi_tool_round_still_uses_asyncio_gather():
    significant, insignificant, _ = validate_csv(FIXTURE_CSV)
    responses = [
        FakeResponse(
            stop_reason="tool_use",
            content=[
                {
                    "type": "tool_use",
                    "id": "toolu_1",
                    "name": "search_slack",
                    "input": {"period": "November 2024", "line_item": "Revenue"},
                },
                {
                    "type": "tool_use",
                    "id": "toolu_2",
                    "name": "search_gmail",
                    "input": {"period": "November 2024", "line_item": "Revenue"},
                },
            ],
        ),
        FakeResponse(
            stop_reason="end_turn",
            content=[
                {
                    "type": "text",
                    "text": "EXECUTIVE SUMMARY\nok\nLINE COMMENTARY\nok\nINSIGNIFICANT VARIANCES\nok",
                }
            ],
        ),
    ]
    client = FakeClient(responses)

    async def slow_a(payload: dict) -> str:
        await asyncio.sleep(0.05)
        return f"a:{payload['line_item']}"

    async def slow_b(payload: dict) -> str:
        await asyncio.sleep(0.05)
        return f"b:{payload['line_item']}"

    start = time.perf_counter()
    await run_agent(
        significant_rows=significant,
        insignificant_rows=insignificant,
        client=client,
        tool_registry={"search_slack": slow_a, "search_gmail": slow_b},
    )
    elapsed = time.perf_counter() - start
    assert elapsed < 0.10
