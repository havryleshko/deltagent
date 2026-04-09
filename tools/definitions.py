from __future__ import annotations


TOOL_DEFINITIONS = [
    {
        "name": "search_slack",
        "description": (
            "Finds operational context in team chat for significant variance lines, "
            "including informal updates, blockers, and implementation decisions. "
            "Use it to corroborate timing or operational context from Gmail or CRM when a line would otherwise be single-source. "
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
            "including salary/headcount decisions, invoices, one-off spend approvals, and secondary recovery or insurance context that may live in a different thread from the main invoice. "
            "Broad and narrow Gmail searches often surface different messages for the same line item. "
            "Use it to corroborate approvals, invoice packs, or secondary context when CRM or Slack is the only current source family. "
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
            "Finds deal, contract, onboarding, and project context in CRM for revenue and revenue-adjacent variances, "
            "including Revenue, Professional Services, Cost of Revenue, slipped deals, and contractor or project-linked spend. "
            "Use it to corroborate downstream revenue, onboarding, and project-linked commentary when other evidence is only from Gmail or Slack. "
            "Does NOT find salary decisions or unrelated general operating expenses."
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
