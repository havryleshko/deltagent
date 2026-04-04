from __future__ import annotations

import pytest

from agent.agent import run_agent
from ui.app import (
    CommentaryScreen,
    DeltAgentApp,
    FilePickerScreen,
    VarianceScreen,
)


def test_ui_app_import_smoke():
    assert DeltAgentApp.TITLE == "DeltAgent"
    assert FilePickerScreen is not None
    assert VarianceScreen is not None
    assert CommentaryScreen is not None


class FakeMessages:
    def __init__(self, responses: list[object]) -> None:
        self._responses = responses

    async def create(self, **kwargs):
        return self._responses.pop(0)


class FakeClient:
    def __init__(self, responses: list[object]) -> None:
        self.messages = FakeMessages(responses)


class FakeResponse:
    def __init__(self, stop_reason: str, content: list[dict]) -> None:
        self.stop_reason = stop_reason
        self.content = content


@pytest.mark.asyncio
async def test_run_agent_tool_diagnostics_tool_not_found():
    responses = [
        FakeResponse(
            stop_reason="tool_use",
            content=[
                {
                    "type": "tool_use",
                    "id": "toolu_1",
                    "name": "search_slack",
                    "input": {"period": "November 2024", "line_item": "Revenue"},
                }
            ],
        ),
        FakeResponse(
            stop_reason="end_turn",
            content=[
                {
                    "type": "text",
                    "text": (
                        "EXECUTIVE SUMMARY\nx\nLINE COMMENTARY\ny\nINSIGNIFICANT VARIANCES\nz"
                    ),
                }
            ],
        ),
    ]
    client = FakeClient(responses)
    diagnostics: list[str] = []
    text = await run_agent(
        significant_rows=[
            {
                "period": "November 2024",
                "line_item": "Revenue",
                "budget_usd": 100.0,
                "actual_usd": 120.0,
                "variance_usd": 20.0,
                "variance_pct": 20.0,
            }
        ],
        insignificant_rows=[],
        client=client,
        tool_registry={},
        tool_diagnostics=diagnostics,
    )
    assert "EXECUTIVE SUMMARY" in text
    assert diagnostics
    assert any("Tool not found" in entry for entry in diagnostics)
