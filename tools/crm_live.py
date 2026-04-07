from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import httpx

from agent.models import Evidence
from tools.base import envelope_to_text
from tools.period_parse import parse_period_to_utc_range

_HUBSPOT_DEALS = "https://api.hubapi.com/crm/v3/objects/deals"


def _hubspot_token() -> str:
    return (
        os.environ.get("HUBSPOT_PRIVATE_APP_TOKEN", "").strip()
        or os.environ.get("HUBSPOT_API_KEY", "").strip()
    )


def _salesforce_env_present() -> bool:
    return bool(
        os.environ.get("SALESFORCE_USERNAME", "").strip()
        and os.environ.get("SALESFORCE_PASSWORD", "").strip()
        and os.environ.get("SALESFORCE_SECURITY_TOKEN", "").strip()
    )


def search_crm_sync(payload: dict[str, Any]) -> str:
    period = str(payload.get("period", ""))
    line_item = str(payload.get("line_item", ""))
    query = str(payload.get("query", ""))
    date_start = str(payload.get("date_start", ""))
    date_end = str(payload.get("date_end", ""))
    token = _hubspot_token()
    if token:
        return _hubspot_deals_sync(period, line_item, query, token)
    if _salesforce_env_present():
        return envelope_to_text(
            tool_name="search_crm",
            period=period,
            date_start=date_start,
            date_end=date_end,
            summary_for_model=(
                "search_crm (live): Salesforce env vars are set but Salesforce is not "
                "implemented; configure HUBSPOT_PRIVATE_APP_TOKEN (or HUBSPOT_API_KEY) "
                "for HubSpot deal search, or use DELTAGENT_TOOL_MODE=mock."
            ),
            error="salesforce_not_implemented",
        )
    return envelope_to_text(
        tool_name="search_crm",
        period=period,
        date_start=date_start,
        date_end=date_end,
        summary_for_model=(
            "search_crm (live): Set HUBSPOT_PRIVATE_APP_TOKEN or HUBSPOT_API_KEY "
            "for HubSpot CRM search."
        ),
        error="missing_hubspot_token",
    )


def _parse_hs_date(value: str | None) -> datetime | None:
    if not value:
        return None
    raw = str(value).strip()
    if raw.isdigit():
        try:
            ms = int(raw)
            return datetime.utcfromtimestamp(ms / 1000.0)
        except (OSError, ValueError, OverflowError):
            return None
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw[:26], fmt)
        except ValueError:
            continue
    return None


def _hubspot_deals_sync(
    period: str, line_item: str, query: str, token: str
) -> str:
    date_start = ""
    date_end = ""
    parsed = None
    if period:
        parsed = parse_period_to_utc_range(period)
        if parsed:
            date_start, date_end = parsed
    if not parsed:
        return envelope_to_text(
            tool_name="search_crm",
            period=period,
            date_start=date_start,
            date_end=date_end,
            summary_for_model=(
                f"search_crm (live): Unparsed period {period!r}; "
                "use a month label like 'November 2024'."
            ),
            error="unparsed_period",
        )
    start_iso, end_iso = parsed
    start_dt = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
    target_year_month = (start_dt.year, start_dt.month)
    try:
        response = httpx.get(
            _HUBSPOT_DEALS,
            params={
                "limit": "100",
                "properties": "dealname,amount,closedate,dealstage",
                "archived": "false",
            },
            headers={"Authorization": f"Bearer {token}"},
            timeout=30.0,
        )
    except httpx.HTTPError as error:
        return envelope_to_text(
            tool_name="search_crm",
            period=period,
            date_start=date_start,
            date_end=date_end,
            summary_for_model=f"HubSpot request failed (live): {error}",
            error="hubspot_http_error",
        )
    if response.status_code >= 400:
        return envelope_to_text(
            tool_name="search_crm",
            period=period,
            date_start=date_start,
            date_end=date_end,
            summary_for_model=f"HubSpot API error (live): {response.status_code} {response.text[:300]}",
            error="hubspot_api_error",
        )
    data = response.json()
    results = data.get("results") or []
    in_month: list[dict[str, Any]] = []
    for deal in results:
        props = deal.get("properties") or {}
        close_raw = props.get("closedate")
        close_dt = _parse_hs_date(close_raw)
        if close_dt is None:
            continue
        if (close_dt.year, close_dt.month) == target_year_month:
            in_month.append(deal)
    if not in_month:
        return envelope_to_text(
            tool_name="search_crm",
            period=period,
            date_start=date_start,
            date_end=date_end,
            summary_for_model=(
                f"No HubSpot deals with closedate in parsed range for {period!r} (live). "
                f"line_item={line_item!r} query={query!r}"
            ),
            error="no_matches",
        )
    kw = (query + " " + line_item).lower()
    evidence: list[Evidence] = []
    summary_lines: list[str] = []
    for deal in in_month:
        props = deal.get("properties") or {}
        name = (props.get("dealname") or "")[:120]
        amt = props.get("amount", "")
        stage = props.get("dealstage", "")
        close = props.get("closedate", "")
        blob = f"{name} {stage}".lower()
        if kw.strip() and len(kw) > 2:
            if not any(len(w) > 2 and w in blob for w in kw.split()):
                continue
        summary_lines.append(f"{name} | amount={amt} | stage={stage} | close={close}")
        evidence.append(
            Evidence(
                id=f"crm-{deal.get('id', name)}",
                source_type="crm",
                timestamp=close,
                snippet=f"{name} amount={amt} stage={stage}",
                ref=name,
            )
        )
    if not summary_lines:
        for deal in in_month[:10]:
            props = deal.get("properties") or {}
            name = (props.get("dealname") or "")[:120]
            close = props.get("closedate", "")
            summary_lines.append(f"{name} | close={close}")
            evidence.append(
                Evidence(
                    id=f"crm-{deal.get('id', name)}",
                    source_type="crm",
                    timestamp=close,
                    snippet=f"{name} | close={close}",
                    ref=name,
                )
            )
    return envelope_to_text(
        tool_name="search_crm",
        period=period,
        date_start=date_start,
        date_end=end_iso,
        summary_for_model="; ".join(summary_lines[:10]),
        evidence=evidence[:10],
    )
