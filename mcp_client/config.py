from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


_DEFAULT_CONFIG_PATH = Path("deltaagent.toml")
_STATE_DIR = Path.home() / ".deltaagent" / "mcp_client"


@dataclass
class McpServerConfig:
    name: str
    url: str
    enabled: bool = True

    @property
    def state_path(self) -> Path:
        return _STATE_DIR / f"{self.name}.json"

    @property
    def is_connected(self) -> bool:
        return self.state_path.is_file()


def load_mcp_servers(config_path: Path | None = None) -> list[McpServerConfig]:
    path = config_path or _DEFAULT_CONFIG_PATH
    if not path.is_file():
        return []
    try:
        with path.open("rb") as fh:
            data = tomllib.load(fh)
    except Exception:
        return []
    servers = []
    for entry in data.get("mcp_servers", []):
        name = str(entry.get("name", "")).strip()
        url = str(entry.get("url", "")).strip()
        if name and url:
            servers.append(
                McpServerConfig(
                    name=name,
                    url=url,
                    enabled=bool(entry.get("enabled", True)),
                )
            )
    return servers


def save_mcp_connection_state(server: McpServerConfig, tools: list[str]) -> None:
    import json

    _STATE_DIR.mkdir(parents=True, exist_ok=True)
    server.state_path.write_text(
        json.dumps({"name": server.name, "url": server.url, "tools": tools}, indent=2),
        encoding="utf-8",
    )


def load_mcp_connection_state(server: McpServerConfig) -> dict | None:
    import json

    if not server.state_path.is_file():
        return None
    try:
        return json.loads(server.state_path.read_text(encoding="utf-8"))
    except Exception:
        return None


def remove_mcp_connection_state(server: McpServerConfig) -> None:
    try:
        server.state_path.unlink(missing_ok=True)
    except OSError:
        pass
