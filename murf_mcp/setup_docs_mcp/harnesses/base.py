from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from murf_mcp.setup_docs_mcp.paths import which

Method = Literal["merged", "created", "updated"]


@dataclass(frozen=True)
class DetectInfo:
    binary: str | None
    config_paths: tuple[str, ...]
    found: bool
    detail: str


@dataclass(frozen=True)
class InstallResult:
    harness_id: str
    label: str
    ok: bool
    method: Method | None
    message: str


def detect_harness(
    binary_name: str | None,
    candidates: list[Path],
    *,
    extra_dir: Path | None = None,
    extra_detail: str = "data found",
) -> DetectInfo:
    """Shared detection: CLI on PATH, an existing config, or a known data dir."""
    binary = which(binary_name) if binary_name else None
    configs = tuple(str(path) for path in candidates if path.is_file())
    has_dir = extra_dir is not None and extra_dir.is_dir()
    found = binary is not None or bool(configs) or has_dir
    if binary:
        detail = f"cli {binary}"
    elif configs:
        detail = "config found"
    elif has_dir:
        detail = extra_detail
    else:
        detail = "not detected"
    return DetectInfo(binary=binary, config_paths=configs, found=found, detail=detail)


_VERB: dict[Method, tuple[str, str]] = {
    "created": ("create", "created"),
    "updated": ("update", "updated"),
    "merged": ("merge into", "merged into"),
}


def result_from_action(
    harness_id: str,
    label: str,
    action: Method,
    shown: str,
    *,
    extra: str | None = None,
    dry_run: bool = False,
) -> InstallResult:
    """Build a successful InstallResult, wording it for real vs. dry runs."""
    present, past = _VERB[action]
    verb = f"would {present}" if dry_run else past
    suffix = f" ({extra})" if extra else ""
    return InstallResult(harness_id, label, True, action, f"{verb} {shown}{suffix}")
