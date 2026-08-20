"""Install Murf docs MCP into Cursor, Claude Code, Claude Desktop, and Codex."""

from __future__ import annotations

import argparse
import platform
import sys

from murf_mcp.setup_docs_mcp.constants import DOCS_MCP_URL, SERVER_NAME
from murf_mcp.setup_docs_mcp.harnesses import BY_ID, HARNESSES
from murf_mcp.setup_docs_mcp.harnesses.base import InstallResult
from murf_mcp.setup_docs_mcp.tui import Choice, run_detected_wizard
from murf_mcp.setup_docs_mcp.tui.ansi import bold, dim, italic

_IDS = tuple(module.ID for module in HARNESSES)


def _os_label() -> str:
    system = platform.system()
    if system == "Darwin":
        return "macOS"
    if system == "Windows":
        return "Windows"
    if system == "Linux":
        return "Linux"
    return system or "unknown"


def _parse_harnesses(value: str) -> list[str]:
    ids: list[str] = []
    for token in value.split(","):
        harness_id = token.strip().lower()
        if not harness_id:
            continue
        if harness_id not in BY_ID:
            known = ", ".join(_IDS)
            raise argparse.ArgumentTypeError(
                f"unknown harness {harness_id!r}; choose from {known}"
            )
        if harness_id not in ids:
            ids.append(harness_id)
    if not ids:
        raise argparse.ArgumentTypeError("no harnesses selected")
    return ids


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="setup-murf-mcp-docs",
        description=(
            "Install the hosted Murf docs MCP into local agent harnesses. "
            "Uses each harness CLI when available, otherwise merges a validated "
            "mcpServers / mcp_servers config file."
        ),
    )
    parser.add_argument(
        "--harnesses",
        type=_parse_harnesses,
        help="comma-separated ids: " + ",".join(_IDS),
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="install into every harness (skips the prompt)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="preview changes without writing any files or running harness CLIs",
    )
    return parser


def _detected_choices() -> list[Choice]:
    choices: list[Choice] = []
    for module in HARNESSES:
        info = module.detect()
        if not info.found:
            continue
        choices.append(
            Choice(id=module.ID, title=module.LABEL, subtitle=info.detail)
        )
    return choices


def _choose(args: argparse.Namespace) -> list[str] | None:
    if args.all:
        return list(_IDS)
    if args.harnesses:
        return args.harnesses

    choices = _detected_choices()
    if not choices:
        print(italic("No harnesses detected on this machine."))
        print(dim("Pass --harnesses cursor,claude-code,claude-desktop,codex to install anyway."))
        sys.exit(1)

    try:
        return run_detected_wizard(choices)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)


def _print_header() -> None:
    print(f"{bold('Murf docs MCP')}  {dim('setup')}")
    print(f"  {dim('OS')}      {_os_label()}")
    print(f"  {dim('Server')}  {SERVER_NAME}")
    print(f"  {dim('URL')}     {italic(DOCS_MCP_URL)}")
    print()


def _print_result(result: InstallResult) -> None:
    status = "ok" if result.ok else "fail"
    method = result.method or "-"
    print(f"  [{status}] {result.label} ({method}): {result.message}")


def main() -> None:
    args = _build_parser().parse_args()
    _print_header()
    if args.dry_run:
        print(italic("Dry run — no files will be written."))
        print()

    try:
        selected = _choose(args)
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(130)

    if selected is None:
        print("Cancelled.")
        sys.exit(130)
    if not selected:
        print("Nothing selected.")
        return

    print(bold("Previewing…" if args.dry_run else "Installing…"))
    results = [BY_ID[harness_id].install(dry_run=args.dry_run) for harness_id in selected]
    print()
    for result in results:
        _print_result(result)

    if any(not result.ok for result in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
