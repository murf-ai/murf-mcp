from murf_mcp.setup_docs_mcp.constants import DOCS_MCP_URL, SERVER_NAME
from murf_mcp.setup_docs_mcp.harnesses.base import (
    DetectInfo,
    InstallResult,
    detect_harness,
    result_from_action,
)
from murf_mcp.setup_docs_mcp.merge_json import upsert_server
from murf_mcp.setup_docs_mcp.paths import claude_code_json_candidates
from murf_mcp.setup_docs_mcp.process import display_path, run_cli
from murf_mcp.setup_docs_mcp.targets import pick_json_target

ID = "claude-code"
LABEL = "Claude Code"

_ENTRY = {"type": "http", "url": DOCS_MCP_URL}


def detect() -> DetectInfo:
    return detect_harness("claude", claude_code_json_candidates())


def _via_cli(binary: str) -> None:
    run_cli(
        [
            binary,
            "mcp",
            "add",
            "--scope",
            "user",
            "--transport",
            "http",
            SERVER_NAME,
            DOCS_MCP_URL,
        ]
    )


def _via_file(dry_run: bool = False) -> InstallResult:
    candidates = claude_code_json_candidates()
    try:
        path = pick_json_target(candidates)
        action = upsert_server(path, _ENTRY, allow_missing_key=True, dry_run=dry_run)
    except ValueError as exc:
        return InstallResult(ID, LABEL, False, None, str(exc))

    return result_from_action(ID, LABEL, action, display_path(path), dry_run=dry_run)


def install(dry_run: bool = False) -> InstallResult:
    info = detect()
    if info.binary and not dry_run:
        _via_cli(info.binary)
    file_result = _via_file(dry_run=dry_run)
    if file_result.ok:
        return file_result
    if info.binary:
        return InstallResult(
            ID,
            LABEL,
            False,
            None,
            "claude mcp add failed and no mcpServers object found to merge",
        )
    return file_result
