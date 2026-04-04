from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable

from agent.prompts import build_system_prompt, build_user_message
from tools.definitions import TOOL_DEFINITIONS


ToolHandler = Callable[[dict[str, Any]], Awaitable[str]]


def _block_value(block: Any, key: str, default: Any = None) -> Any:
    if isinstance(block, dict):
        return block.get(key, default)
    return getattr(block, key, default)


async def _execute_tool_call(
    tool_call: Any, tool_registry: dict[str, ToolHandler]
) -> dict[str, Any]:
    tool_name = _block_value(tool_call, "name", "")
    tool_use_id = _block_value(tool_call, "id", "")
    tool_input = _block_value(tool_call, "input", {}) or {}
    handler = tool_registry.get(tool_name)
    if handler is None:
        content = f"Tool not found: {tool_name}"
    else:
        try:
            content = await handler(tool_input)
            if not isinstance(content, str):
                content = str(content)
        except Exception as error:
            content = f"Tool error ({tool_name}): {error}"
    return {"type": "tool_result", "tool_use_id": tool_use_id, "content": content}


def _extract_text(response: Any) -> str:
    content = getattr(response, "content", []) or []
    text_blocks = []
    for block in content:
        if _block_value(block, "type") == "text":
            text_value = _block_value(block, "text", "")
            if text_value:
                text_blocks.append(text_value)
    return "\n".join(text_blocks).strip()


async def run_agent(
    significant_rows: list[dict[str, Any]],
    insignificant_rows: list[dict[str, Any]],
    client: Any | None = None,
    tool_registry: dict[str, ToolHandler] | None = None,
    model: str = "claude-sonnet-4-6",
    max_rounds: int = 8,
    tool_diagnostics: list[str] | None = None,
) -> str:
    tool_registry = tool_registry or {}
    if client is None:
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic()

    messages: list[dict[str, Any]] = [
        {
            "role": "user",
            "content": build_user_message(
                significant_rows=significant_rows,
                insignificant_rows=insignificant_rows,
            ),
        }
    ]

    tools: list[dict[str, Any]] = [
        definition
        for definition in TOOL_DEFINITIONS
        if definition["name"] in tool_registry
    ]

    rounds = 0
    while True:
        rounds += 1
        if rounds > max_rounds:
            return "No context found — recommend review"

        response = await client.messages.create(
            model=model,
            max_tokens=1800,
            system=build_system_prompt(),
            messages=messages,
            tools=tools,
        )

        assistant_content = getattr(response, "content", []) or []
        messages.append({"role": "assistant", "content": assistant_content})

        stop_reason = getattr(response, "stop_reason", None)
        if stop_reason != "tool_use":
            text = _extract_text(response)
            return text or "No context found — recommend review"

        tool_calls = [
            block for block in assistant_content if _block_value(block, "type") == "tool_use"
        ]
        if not tool_calls:
            return "No context found — recommend review"

        tool_results = await asyncio.gather(
            *[_execute_tool_call(tool_call, tool_registry) for tool_call in tool_calls]
        )
        if tool_diagnostics is not None:
            for tool_call, result in zip(tool_calls, tool_results):
                content = result.get("content", "")
                if isinstance(content, str) and (
                    content.startswith("Tool error")
                    or content.startswith("Tool not found")
                ):
                    name = _block_value(tool_call, "name", "unknown")
                    tool_diagnostics.append(f"{name}: {content}")
        messages.append({"role": "user", "content": tool_results})
