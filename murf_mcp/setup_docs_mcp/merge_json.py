import json
from pathlib import Path
from typing import Any

from murf_mcp.setup_docs_mcp.constants import SERVER_NAME


def _read_object(path: Path) -> dict[str, Any] | None:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return None
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    return data


def find_file_with_servers(candidates: list[Path], key: str = "mcpServers") -> Path | None:
    """Return the first existing file that already has a servers object."""
    for path in candidates:
        if not path.is_file():
            continue
        data = _read_object(path)
        if data is None:
            continue
        servers = data.get(key)
        if isinstance(servers, dict):
            return path
    return None


def upsert_server(
    path: Path,
    entry: dict[str, Any],
    *,
    key: str = "mcpServers",
    name: str = SERVER_NAME,
    allow_missing_key: bool = False,
    dry_run: bool = False,
) -> str:
    """
    Merge `entry` under mcpServers[name], always rewriting our server.

    Existing files must already contain `key`, unless they are empty `{}`
    or `allow_missing_key` is set for a well-known config path.
    """
    if path.is_file():
        data = _read_object(path)
        if data is None:
            raise ValueError(f"Not valid JSON: {path}")
        if key in data and not isinstance(data.get(key), dict):
            raise ValueError(f"{key!r} exists but is not an object in {path}")
        if key not in data:
            if not allow_missing_key and data:
                raise ValueError(f"No {key!r} object in {path}")
            data[key] = {}
        servers = data[key]
        existed = name in servers
        servers[name] = entry
        action = "updated" if existed else "merged"
    else:
        data = {key: {name: entry}}
        action = "created"

    if dry_run:
        return action
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return action
