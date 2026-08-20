from murf_mcp.setup_docs_mcp.constants import DOCS_MCP_URL
from murf_mcp.setup_docs_mcp.harnesses.base import (
    DetectInfo,
    InstallResult,
    detect_harness,
    result_from_action,
)
from murf_mcp.setup_docs_mcp.merge_json import upsert_server
from murf_mcp.setup_docs_mcp.paths import cursor_dir, cursor_mcp_candidates
from murf_mcp.setup_docs_mcp.process import display_path
from murf_mcp.setup_docs_mcp.targets import pick_json_target

ID = "cursor"
LABEL = "Cursor"

_ENTRY = {"url": DOCS_MCP_URL}


def detect() -> DetectInfo:
    return detect_harness(
        "cursor",
        cursor_mcp_candidates(),
        extra_dir=cursor_dir(),
        extra_detail="Cursor data found",
    )


def install(dry_run: bool = False) -> InstallResult:
    candidates = cursor_mcp_candidates()
    try:
        path = pick_json_target(candidates)
        action = upsert_server(path, _ENTRY, dry_run=dry_run)
    except ValueError as exc:
        return InstallResult(ID, LABEL, False, None, str(exc))

    return result_from_action(
        ID, LABEL, action, display_path(path), extra="reload Cursor", dry_run=dry_run
    )
