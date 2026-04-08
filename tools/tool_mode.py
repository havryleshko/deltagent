from __future__ import annotations

import os


def is_live_tool_mode() -> bool:
    return os.environ.get("DELTAGENT_TOOL_MODE", "mock").strip().lower() == "live"
