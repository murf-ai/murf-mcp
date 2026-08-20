import subprocess
from pathlib import Path

from murf_mcp.setup_docs_mcp.paths import which


def run_cli(argv: list[str], *, timeout: int = 45) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return 127, f"command not found: {argv[0]}"
    except subprocess.TimeoutExpired:
        return 124, f"timed out: {' '.join(argv)}"
    output = "\n".join(
        part.strip()
        for part in (completed.stdout, completed.stderr)
        if part and part.strip()
    )
    return completed.returncode, output


def npx_bin() -> str | None:
    return which("npx")


def display_path(path: Path) -> str:
    try:
        return str(path.expanduser())
    except OSError:
        return str(path)
