from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("DELTAGENT_RUN_LIVE_INTEGRATION_TESTS", "") != "1",
    reason="Set DELTAGENT_RUN_LIVE_INTEGRATION_TESTS=1 to run live integration checks",
)


@pytest.mark.asyncio
async def test_live_crm_hubspot_placeholder() -> None:
    if not (
        os.environ.get("HUBSPOT_PRIVATE_APP_TOKEN", "").strip()
        or os.environ.get("HUBSPOT_API_KEY", "").strip()
    ):
        pytest.skip("HubSpot token not configured")
    from tools.crm_tool import search_crm

    out = await search_crm(
        {
            "period": "November 2024",
            "line_item": "Revenue",
            "query": "deal",
        }
    )
    assert isinstance(out, str)
    assert len(out) > 0
