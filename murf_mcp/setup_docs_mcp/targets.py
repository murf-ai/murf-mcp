from pathlib import Path

from murf_mcp.setup_docs_mcp.merge_json import find_file_with_servers as find_json_servers
from murf_mcp.setup_docs_mcp.merge_toml import find_file_with_servers as find_toml_servers


def pick_json_target(candidates: list[Path]) -> Path:
    """Prefer a file that already has mcpServers; else the canonical path."""
    found = find_json_servers(candidates)
    if found is not None:
        return found
    if not candidates:
        raise ValueError("No config path candidates")
    return candidates[0]


def pick_toml_target(candidates: list[Path]) -> Path:
    found = find_toml_servers(candidates)
    if found is not None:
        return found
    if not candidates:
        raise ValueError("No config path candidates")
    return candidates[0]
