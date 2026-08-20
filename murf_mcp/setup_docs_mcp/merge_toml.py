import tomllib
from pathlib import Path
from typing import Any

from murf_mcp.setup_docs_mcp.constants import DOCS_MCP_URL, SERVER_NAME

_TABLE = f"""
[mcp_servers.{SERVER_NAME}]
url = "{DOCS_MCP_URL}"
enabled = true
"""


def _read_toml(path: Path) -> dict[str, Any] | None:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return None
    if not raw.strip():
        return {}
    try:
        return tomllib.loads(raw)
    except tomllib.TOMLDecodeError:
        return None


def find_file_with_servers(candidates: list[Path]) -> Path | None:
    for path in candidates:
        if not path.is_file():
            continue
        data = _read_toml(path)
        if data is None:
            continue
        servers = data.get("mcp_servers")
        if isinstance(servers, dict):
            return path
    return None


def _table_block() -> str:
    return _TABLE.strip("\n") + "\n"


def _header_inner(line: str) -> str | None:
    """Return the dotted key inside a table header line, else None."""
    stripped = line.strip()
    if not stripped.startswith("["):
        return None
    body = stripped.lstrip("[")
    end = body.find("]")
    if end == -1:
        return None
    return body[:end].strip()


def _is_our_table(inner: str, name: str) -> bool:
    """True if a header targets [mcp_servers.<name>] or a sub-table of it."""
    for prefix in (f"mcp_servers.{name}", f'mcp_servers."{name}"'):
        if inner == prefix or inner.startswith(prefix + "."):
            return True
    return False


def _is_blank_or_comment(line: str) -> bool:
    stripped = line.strip()
    return not stripped or stripped.startswith("#")


def _strip_our_tables(text: str, name: str) -> tuple[str, bool]:
    """
    Remove the [mcp_servers.<name>] table and any of its sub-tables.

    Handles bare and quoted-key headers. Trailing blank/comment lines that sit
    right before the next unrelated table are preserved, since they usually
    document that following table rather than ours.
    """
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    index = 0
    removed = False
    while index < len(lines):
        inner = _header_inner(lines[index])
        if inner is not None and _is_our_table(inner, name):
            removed = True
            start = index
            index += 1
            while index < len(lines):
                nxt = _header_inner(lines[index])
                if nxt is not None and not _is_our_table(nxt, name):
                    break
                index += 1
            block = lines[start:index]
            trailing: list[str] = []
            while block and _is_blank_or_comment(block[-1]):
                trailing.insert(0, block.pop())
            out.extend(trailing)
        else:
            out.append(lines[index])
            index += 1
    return "".join(out), removed


def upsert_server(
    path: Path,
    *,
    name: str = SERVER_NAME,
    allow_missing_key: bool = False,
    dry_run: bool = False,
) -> str:
    """
    Write [mcp_servers.<name>] with the current docs MCP URL.

    Any existing table for `name` (including its sub-tables and quoted-key
    forms) is removed first, so re-runs always pick up URL changes. Other
    tables and comments in the file are left intact.
    """
    block = _table_block()
    if path.is_file():
        data = _read_toml(path)
        if data is None:
            raise ValueError(f"Not valid TOML: {path}")
        servers = data.get("mcp_servers")
        if "mcp_servers" not in data:
            if not allow_missing_key and data:
                raise ValueError(f"No 'mcp_servers' table in {path}")
            servers = {}
        if not isinstance(servers, dict):
            raise ValueError(f"'mcp_servers' exists but is not a table in {path}")

        existed = name in servers
        text = path.read_text(encoding="utf-8")
        stripped, _ = _strip_our_tables(text, name)
        stripped = stripped.rstrip("\n")
        new_text = f"{stripped}\n\n{block}" if stripped else block
        if not dry_run:
            path.write_text(new_text, encoding="utf-8")
        return "updated" if existed else "merged"

    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(block, encoding="utf-8")
    return "created"
