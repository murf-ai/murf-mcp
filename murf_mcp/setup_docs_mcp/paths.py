import os
import shutil
import sys
from pathlib import Path


def home() -> Path:
    return Path.home()


def which(name: str) -> str | None:
    return shutil.which(name)


def env_path(name: str) -> Path | None:
    value = os.environ.get(name)
    if not value:
        return None
    return Path(value).expanduser()


def _dedupe(paths: list[Path]) -> list[Path]:
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        unique.append(path)
    return unique


def cursor_dir() -> Path:
    return home() / ".cursor"


def cursor_mcp_candidates() -> list[Path]:
    paths = [cursor_dir() / "mcp.json"]
    appdata = env_path("APPDATA")
    if appdata:
        paths.append(appdata / "Cursor" / "mcp.json")
    return _dedupe(paths)


def claude_code_json_candidates() -> list[Path]:
    paths: list[Path] = []
    config_dir = env_path("CLAUDE_CONFIG_DIR")
    if config_dir:
        paths.append(config_dir / ".claude.json")
    paths.append(home() / ".claude.json")
    return _dedupe(paths)


def claude_desktop_config_candidates() -> list[Path]:
    if sys.platform == "win32":
        appdata = env_path("APPDATA")
        if not appdata:
            return []
        return [appdata / "Claude" / "claude_desktop_config.json"]
    if sys.platform == "darwin":
        return [
            home()
            / "Library"
            / "Application Support"
            / "Claude"
            / "claude_desktop_config.json"
        ]
    return []


def claude_desktop_dir() -> Path | None:
    candidates = claude_desktop_config_candidates()
    if not candidates:
        return None
    return candidates[0].parent


def codex_config_candidates() -> list[Path]:
    paths: list[Path] = []
    codex_home = env_path("CODEX_HOME")
    if codex_home:
        paths.append(codex_home / "config.toml")
    paths.append(home() / ".codex" / "config.toml")
    return _dedupe(paths)
