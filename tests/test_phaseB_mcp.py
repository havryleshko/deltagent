from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_client.config import (
    McpServerConfig,
    load_mcp_servers,
    save_mcp_connection_state,
    load_mcp_connection_state,
    remove_mcp_connection_state,
)
from mcp_client.registry import mcp_tool_to_definition, _make_mcp_handler


def test_server_config_is_connected_false_by_default(tmp_path):
    server = McpServerConfig(name="test", url="https://example.com/sse")
    assert not server.is_connected


def test_save_and_load_connection_state(tmp_path, monkeypatch):
    monkeypatch.setattr("mcp_client.config._STATE_DIR", tmp_path)
    server = McpServerConfig(name="xero", url="https://mcp.xero.com/sse")
    save_mcp_connection_state(server, ["search_transactions", "list_accounts"])
    state = load_mcp_connection_state(server)
    assert state is not None
    assert state["tools"] == ["search_transactions", "list_accounts"]


def test_remove_connection_state(tmp_path, monkeypatch):
    monkeypatch.setattr("mcp_client.config._STATE_DIR", tmp_path)
    server = McpServerConfig(name="xero", url="https://mcp.xero.com/sse")
    save_mcp_connection_state(server, ["tool_a"])
    remove_mcp_connection_state(server)
    assert load_mcp_connection_state(server) is None


def test_load_mcp_servers_empty_when_no_file():
    servers = load_mcp_servers(Path("/nonexistent/deltaagent.toml"))
    assert servers == []


def test_load_mcp_servers_parses_toml(tmp_path):
    config = tmp_path / "deltaagent.toml"
    config.write_text(
        '[[mcp_servers]]\nname = "xero"\nurl = "https://mcp.xero.com/sse"\n'
        '[[mcp_servers]]\nname = "light"\nurl = "https://mcp.light.inc/sse"\n',
        encoding="utf-8",
    )
    servers = load_mcp_servers(config)
    assert len(servers) == 2
    assert servers[0].name == "xero"
    assert servers[1].url == "https://mcp.light.inc/sse"


def test_load_mcp_servers_disabled_entry(tmp_path):
    config = tmp_path / "deltaagent.toml"
    config.write_text(
        '[[mcp_servers]]\nname = "xero"\nurl = "https://mcp.xero.com/sse"\nenabled = false\n',
        encoding="utf-8",
    )
    servers = load_mcp_servers(config)
    assert len(servers) == 1
    assert not servers[0].enabled


def test_load_mcp_servers_skips_incomplete_entries(tmp_path):
    config = tmp_path / "deltaagent.toml"
    config.write_text('[[mcp_servers]]\nname = "no_url"\n', encoding="utf-8")
    servers = load_mcp_servers(config)
    assert servers == []


def test_mcp_tool_to_definition_format():
    tool = {
        "name": "search_transactions",
        "description": "Search financial transactions",
        "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}},
    }
    defn = mcp_tool_to_definition("xero", tool)
    assert defn["name"] == "search_transactions"
    assert "xero" in defn["description"]
    assert defn["input_schema"]["type"] == "object"


@pytest.mark.asyncio
async def test_mcp_handler_returns_envelope_on_success():
    server = McpServerConfig(name="xero", url="https://mcp.xero.com/sse")
    with patch("mcp_client.registry.mcp_client") as mock_client:
        mock_client.call_tool = AsyncMock(return_value="Sales: £11,003 vs £6,000 budget")
        handler = _make_mcp_handler(server, "search_transactions")
        result = await handler({"period": "March 2026", "query": "sales"})

    payload = json.loads(result)
    assert payload["tool_name"] == "search_transactions"
    assert "Sales" in payload["summary_for_model"]
    assert payload.get("error") is None


@pytest.mark.asyncio
async def test_mcp_handler_returns_error_envelope_on_failure():
    server = McpServerConfig(name="xero", url="https://mcp.xero.com/sse")
    with patch("mcp_client.registry.mcp_client") as mock_client:
        mock_client.call_tool = AsyncMock(side_effect=ConnectionError("timeout"))
        handler = _make_mcp_handler(server, "search_transactions")
        result = await handler({"period": "March 2026"})

    payload = json.loads(result)
    assert payload.get("error") is not None
    assert "timeout" in payload["summary_for_model"].lower()


@pytest.mark.asyncio
async def test_build_mcp_tool_registry_uses_saved_state_on_failure(tmp_path, monkeypatch):
    monkeypatch.setattr("mcp_client.config._STATE_DIR", tmp_path)
    server = McpServerConfig(name="xero", url="https://mcp.xero.com/sse")
    save_mcp_connection_state(server, ["search_xero_transactions"])

    with patch("mcp_client.registry.mcp_client") as mock_client:
        mock_client.discover_tools = AsyncMock(side_effect=ConnectionError("offline"))
        from mcp_client.registry import build_mcp_tool_registry

        registry, defs = await build_mcp_tool_registry([server])

    assert "search_xero_transactions" in registry
    assert len(defs) == 1


@pytest.mark.asyncio
async def test_build_mcp_tool_registry_empty_when_no_servers():
    from mcp_client.registry import build_mcp_tool_registry

    registry, defs = await build_mcp_tool_registry([])
    assert registry == {}
    assert defs == []


def test_cli_mcp_status_no_config(tmp_path, monkeypatch):
    from typer.testing import CliRunner
    from cli import app

    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(app, ["auth", "mcp-status"])
    assert result.exit_code == 0
    assert "No MCP servers configured" in result.stdout


def test_cli_mcp_status_not_connected(tmp_path, monkeypatch):
    from typer.testing import CliRunner
    from cli import app

    config = tmp_path / "deltaagent.toml"
    config.write_text('[[mcp_servers]]\nname = "xero"\nurl = "https://mcp.xero.com/sse"\n')
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("mcp_client.config._STATE_DIR", tmp_path / "state")
    runner = CliRunner()
    result = runner.invoke(app, ["auth", "mcp-status"])
    assert result.exit_code == 1
    assert "not connected" in result.stdout
