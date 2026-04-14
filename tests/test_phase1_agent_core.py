from __future__ import annotations

import time
from pathlib import Path

import pytest

from agent.agent import run_agent
from agent.prompts import build_system_prompt, build_user_message
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


def test_validate_csv_significance_split():
    significant, insignificant, errors = validate_csv(FIXTURE_CSV)
    assert not errors
    assert {row["line_item"] for row in significant} == {
        "Revenue",
        "Salaries",
        "Professional Fees",
    }
    assert {row["line_item"] for row in insignificant} == {
        "Software & Subscriptions",
        "Office & Facilities",
    }


def test_prompt_contract_sections_present():
    significant, insignificant, _ = validate_csv(FIXTURE_CSV)
    system_prompt = build_system_prompt()
    user_message = build_user_message(significant, insignificant)
    assert "EXECUTIVE SUMMARY" in system_prompt
    assert "LINE COMMENTARY" in system_prompt
    assert "INSIGNIFICANT VARIANCES" in system_prompt
    assert "No context found — recommend review" in system_prompt
    assert "bucket totals" in system_prompt.lower()
    assert "Professional Fees" in user_message
    assert "Full report totals" not in user_message
    assert (
        "Revenue (reported lines) totals:" in user_message
        or "Do not state a single consolidated" in user_message
    )


@pytest.mark.asyncio
async def test_run_agent_tool_loop_with_mocked_client():
    significant, insignificant, _ = validate_csv(FIXTURE_CSV)
    responses = [
        FakeResponse(
            stop_reason="tool_use",
            content=[
                {
                    "type": "tool_use",
                    "id": "toolu_1",
                    "name": "search_slack",
                    "input": {"query": "professional fees november 2024"},
                }
            ],
        ),
        FakeResponse(
            stop_reason="end_turn",
            content=[
                {
                    "type": "text",
                    "text": (
                        "EXECUTIVE SUMMARY\nSummary\n\nLINE COMMENTARY\nProfessional Fees | "
                        "Variance: -$6,000 (-75%)\nNo context found — recommend review\n\n"
                        "INSIGNIFICANT VARIANCES\nOffice & Facilities: +$100 (+2.5%)"
                    ),
                }
            ],
        ),
    ]
    client = FakeClient(responses)

    async def search_slack(_: dict) -> str:
        return "No matching messages"

    output = await run_agent(
        significant_rows=significant,
        insignificant_rows=insignificant,
        client=client,
        tool_registry={"search_slack": search_slack},
    )

    assert "EXECUTIVE SUMMARY" in output.raw_text
    assert "LINE COMMENTARY" in output.raw_text
    assert "INSIGNIFICANT VARIANCES" in output.raw_text
    assert len(client.messages.calls) == 2


@pytest.mark.asyncio
async def test_run_agent_executes_tools_in_parallel():
    significant, insignificant, _ = validate_csv(FIXTURE_CSV)
    responses = [
        FakeResponse(
            stop_reason="tool_use",
            content=[
                {"type": "tool_use", "id": "toolu_1", "name": "search_slack", "input": {}},
                {"type": "tool_use", "id": "toolu_2", "name": "search_gmail", "input": {}},
            ],
        ),
        FakeResponse(
            stop_reason="end_turn",
            content=[{"type": "text", "text": "EXECUTIVE SUMMARY\nx\nLINE COMMENTARY\ny\nINSIGNIFICANT VARIANCES\nz"}],
        ),
    ]
    client = FakeClient(responses)

    async def slow_a(_: dict) -> str:
        await asyncio.sleep(0.05)
        return "a"

    async def slow_b(_: dict) -> str:
        await asyncio.sleep(0.05)
        return "b"

    import asyncio

    start = time.perf_counter()
    await run_agent(
        significant_rows=significant,
        insignificant_rows=insignificant,
        client=client,
        tool_registry={"search_slack": slow_a, "search_gmail": slow_b},
    )
    elapsed = time.perf_counter() - start
    assert elapsed < 0.10


@pytest.mark.asyncio
async def test_professional_fees_phase1_fallback_gate():
    significant, insignificant, _ = validate_csv(FIXTURE_CSV)
    responses = [
        FakeResponse(
            stop_reason="end_turn",
            content=[
                {
                    "type": "text",
                    "text": (
                        "EXECUTIVE SUMMARY\nSummary\n\nLINE COMMENTARY\nProfessional Fees | "
                        "Variance: -$6,000 (-75%)\nNo context found — recommend review\n\n"
                        "INSIGNIFICANT VARIANCES\nOffice & Facilities: +$100 (+2.5%)"
                    ),
                }
            ],
        )
    ]
    client = FakeClient(responses)
    output = await run_agent(
        significant_rows=significant,
        insignificant_rows=insignificant,
        client=client,
        tool_registry={},
    )
    assert "No context found" in output.raw_text or "recommend review" in output.raw_text.lower()
    assert "costs were higher than expected" not in output.raw_text.lower()
