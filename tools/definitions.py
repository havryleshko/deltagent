from __future__ import annotations


TOOL_DEFINITIONS = [
    {
        "name": "search_slack",
        "description": (
            "Finds operational context in team chat for significant variance lines, "
            "including informal updates, blockers, and implementation decisions. "
            "Does NOT find formal approvals, invoice-level accounting evidence, or CRM pipeline data."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {"type": "string"},
                "line_item": {"type": "string"},
                "query": {"type": "string"},
                "search_scope": {"type": "string", "enum": ["broad", "narrow"]},
            },
            "required": ["period", "line_item", "query"],
            "additionalProperties": False,
        },
    },
    {
        "name": "search_gmail",
        "description": (
            "Finds formal decisions and approvals in email for significant variance lines, "
            "including salary/headcount decisions, invoices, and one-off spend approvals. "
            "Does NOT find casual team chat context or CRM opportunity pipeline status."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {"type": "string"},
                "line_item": {"type": "string"},
                "query": {"type": "string"},
                "search_scope": {"type": "string", "enum": ["broad", "narrow"]},
            },
            "required": ["period", "line_item", "query"],
            "additionalProperties": False,
        },
    },
    {
        "name": "search_calendar",
        "description": (
            "Finds timing and schedule context in calendar data for significant variance lines, "
            "including offsites, campaign launches, travel windows, and holidays. "
            "Does NOT find deal pipeline outcomes or cost approval rationale."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {"type": "string"},
                "line_item": {"type": "string"},
                "query": {"type": "string"},
                "search_scope": {"type": "string", "enum": ["broad", "narrow"]},
            },
            "required": ["period", "line_item", "query"],
            "additionalProperties": False,
        },
    },
    {
        "name": "search_crm",
        "description": (
            "Finds revenue-driving context in CRM for significant revenue variances, "
            "including closed/won, slipped deals, and pipeline movement. "
            "Does NOT find cost line explanations, salary decisions, or general operating expenses."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {"type": "string"},
                "line_item": {"type": "string"},
                "query": {"type": "string"},
                "search_scope": {"type": "string", "enum": ["broad", "narrow"]},
            },
            "required": ["period", "line_item", "query"],
            "additionalProperties": False,
        },
    },
]
