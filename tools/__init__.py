from __future__ import annotations

from tools.calendar_tool import search_calendar
from tools.crm_tool import search_crm
from tools.gmail_tool import search_gmail
from tools.slack_tool import search_slack


def build_mock_tool_registry():
    return {
        "search_slack": search_slack,
        "search_gmail": search_gmail,
        "search_calendar": search_calendar,
        "search_crm": search_crm,
    }
