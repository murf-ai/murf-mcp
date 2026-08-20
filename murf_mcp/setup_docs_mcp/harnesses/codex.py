from murf_mcp.setup_docs_mcp.constants import DOCS_MCP_URL, SERVER_NAME
from murf_mcp.setup_docs_mcp.harnesses.base import (
    DetectInfo,
    InstallResult,
    detect_harness,
    result_from_action,
)
from murf_mcp.setup_docs_mcp.merge_toml import upsert_server
from murf_mcp.setup_docs_mcp.paths import codex_config_candidates
from murf_mcp.setup_docs_mcp.process import display_path, run_cli
from murf_mcp.setup_docs_mcp.targets import pick_toml_target

ID = "codex"
LABEL = "OpenAI Codex"


def detect() -> DetectInfo:
    return detect_harness("codex", codex_config_candidates())


def _via_cli(binary: str) -> None:
    run_cli([binary, "mcp", "add", SERVER_NAME, "--url", DOCS_MCP_URL])


def _via_file(dry_run: bool = False) -> InstallResult:
    candidates = codex_config_candidates()
    try:
        path = pick_toml_target(candidates)
        action = upsert_server(path, allow_missing_key=True, dry_run=dry_run)
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
            "codex mcp add failed and no mcp_servers table found to merge",
        )
    return file_result
