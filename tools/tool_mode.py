from __future__ import annotations

import os


def is_live_tool_mode() -> bool:
    """DELTAGENT_TOOL_MODE=live enables real APIs; default mock keeps CI and fixtures stable."""
    return os.environ.get("DELTAGENT_TOOL_MODE", "mock").strip().lower() == "live"
