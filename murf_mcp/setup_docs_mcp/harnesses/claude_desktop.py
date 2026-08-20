import sys

from murf_mcp.setup_docs_mcp.constants import (
    DOCS_MCP_URL,
    MCP_REMOTE_PACKAGE,
    SERVER_NAME,
)
from murf_mcp.setup_docs_mcp.harnesses.base import (
    DetectInfo,
    InstallResult,
    detect_harness,
    result_from_action,
)
from murf_mcp.setup_docs_mcp.merge_json import upsert_server
from murf_mcp.setup_docs_mcp.paths import (
    claude_desktop_config_candidates,
    claude_desktop_dir,
)
from murf_mcp.setup_docs_mcp.process import display_path, npx_bin
from murf_mcp.setup_docs_mcp.targets import pick_json_target

ID = "claude-desktop"
LABEL = "Claude Desktop"


def detect() -> DetectInfo:
    return detect_harness(
        None,
        claude_desktop_config_candidates(),
        extra_dir=claude_desktop_dir(),
        extra_detail="app data found",
    )


def install(dry_run: bool = False) -> InstallResult:
    if sys.platform not in {"darwin", "win32"}:
        return InstallResult(
            ID,
            LABEL,
            False,
            None,
            "Claude Desktop is only supported on macOS and Windows",
        )

    npx = npx_bin()
    if not npx:
        return InstallResult(
            ID,
            LABEL,
            False,
            None,
            "npx not found; install Node.js to bridge the remote docs MCP",
        )

    entry = {
        "command": npx,
        "args": ["-y", MCP_REMOTE_PACKAGE, DOCS_MCP_URL],
    }
    candidates = claude_desktop_config_candidates()
    if not candidates:
        return InstallResult(ID, LABEL, False, None, "no Claude Desktop config path")

    try:
        path = pick_json_target(candidates)
        action = upsert_server(
            path, entry, name=SERVER_NAME, allow_missing_key=True, dry_run=dry_run
        )
    except ValueError as exc:
        return InstallResult(ID, LABEL, False, None, str(exc))

    return result_from_action(
        ID,
        LABEL,
        action,
        display_path(path),
        extra="fully quit and restart Claude Desktop",
        dry_run=dry_run,
    )
