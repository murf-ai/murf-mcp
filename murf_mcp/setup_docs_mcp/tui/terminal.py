from __future__ import annotations

import os
import sys
from collections.abc import Sequence
from typing import Any


def _enable_windows_ansi() -> None:
    if os.name != "nt":
        return
    try:
        import ctypes

        handle = ctypes.windll.kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint()
        if ctypes.windll.kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            ctypes.windll.kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except (AttributeError, OSError):
        return


def require_tty() -> None:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise RuntimeError(
            "not a TTY; pass --harnesses cursor,claude-code,claude-desktop,codex"
        )


class Terminal:
    """Raw TTY session that redraws a block of lines in place."""

    def __init__(self) -> None:
        self._drawn = 0
        self._fd: int | None = None
        self._previous: Any = None

    def __enter__(self) -> Terminal:
        require_tty()
        _enable_windows_ansi()
        self.write("\033[?25l")
        if os.name != "nt":
            import termios
            import tty

            self._fd = sys.stdin.fileno()
            self._previous = termios.tcgetattr(self._fd)
            tty.setraw(self._fd)
        return self

    def __exit__(self, *exc: object) -> None:
        if os.name != "nt" and self._fd is not None and self._previous is not None:
            import termios

            termios.tcsetattr(self._fd, termios.TCSADRAIN, self._previous)
        self.write("\033[?25h")
        self.write("\r\n")

    def write(self, text: str) -> None:
        sys.stdout.write(text)
        sys.stdout.flush()

    def paint(self, lines: Sequence[str]) -> None:
        count = len(lines)
        if self._drawn:
            self.write(f"\033[{self._drawn}A")
        for line in lines:
            self.write(f"\033[2K\r{line}\r\n")
        if self._drawn > count:
            extra = self._drawn - count
            for _ in range(extra):
                self.write("\033[2K\r\r\n")
            self.write(f"\033[{extra}A")
        self._drawn = count

    def read_key(self) -> str:
        if os.name == "nt":
            return _read_key_windows()
        return _read_key_posix()


def _read_key_windows() -> str:
    import msvcrt

    char = msvcrt.getwch()
    if char in {"\x00", "\xe0"}:
        extra = msvcrt.getwch()
        if extra == "H":
            return "up"
        if extra == "P":
            return "down"
        return "ignore"
    if char in {"\r", "\n"}:
        return "enter"
    if char == " ":
        return "space"
    if char == "\x03":
        return "quit"
    if char in {"q", "Q"}:
        return "quit"
    if char in {"a", "A"}:
        return "a"
    if char in {"n", "N"}:
        return "n"
    if char in {"y", "Y"}:
        return "y"
    if char in {"k", "K"}:
        return "up"
    if char in {"j", "J"}:
        return "down"
    return "ignore"


def _read_key_posix() -> str:
    char = sys.stdin.read(1)
    if char == "\x1b":
        rest = sys.stdin.read(2)
        if rest == "[A":
            return "up"
        if rest == "[B":
            return "down"
        return "ignore"
    if char in {"\r", "\n"}:
        return "enter"
    if char == " ":
        return "space"
    if char in {"\x03", "\x04"}:
        return "quit"
    if char in {"q", "Q"}:
        return "quit"
    if char in {"a", "A"}:
        return "a"
    if char in {"n", "N"}:
        return "n"
    if char in {"y", "Y"}:
        return "y"
    if char in {"k", "K"}:
        return "up"
    if char in {"j", "J"}:
        return "down"
    return "ignore"
