from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from murf_mcp.setup_docs_mcp.tui.ansi import (
    CHECKED,
    POINTER,
    UNCHECKED,
    bold,
    cyan,
    dim,
    italic,
    keycap,
)
from murf_mcp.setup_docs_mcp.tui.terminal import Terminal

Action = Literal["next", "back", "quit"]


@dataclass(frozen=True)
class Choice:
    id: str
    title: str
    subtitle: str


@dataclass(frozen=True)
class ScreenResult:
    action: Action
    selected: tuple[str, ...] = ()


def _hint(*parts: tuple[str, str]) -> str:
    chunks = [f"{keycap(key)} {dim(label)}" for key, label in parts]
    return f" {dim('│')} ".join(chunks)


def _select_title(count: int) -> str:
    noun = "harness" if count == 1 else "harnesses"
    return (
        f"Detected {count} {noun}. "
        "Choose where to install the Murf docs MCP."
    )


def _checkbox_lines(
    choices: list[Choice],
    checked: list[bool],
    cursor: int,
) -> list[str]:
    lines = [
        bold(_select_title(len(choices))),
        "",
    ]
    for index, choice in enumerate(choices):
        pointer = cyan(POINTER) if index == cursor else " "
        mark = CHECKED if checked[index] else UNCHECKED
        title = bold(choice.title) if index == cursor else choice.title
        lines.append(f" {pointer} {mark}  {title}  {italic(dim(choice.subtitle))}")
    lines.extend(
        [
            "",
            _hint(
                ("↑/↓", "move"),
                ("space", "toggle"),
                ("a", "all"),
                ("n", "none"),
                ("enter", "next"),
                ("q", "quit"),
            ),
        ]
    )
    return lines


def checkbox_screen(
    term: Terminal,
    choices: list[Choice],
    checked: list[bool],
) -> ScreenResult:
    cursor = 0
    term.paint(_checkbox_lines(choices, checked, cursor))
    while True:
        key = term.read_key()
        if key == "up":
            cursor = (cursor - 1) % len(choices)
        elif key == "down":
            cursor = (cursor + 1) % len(choices)
        elif key == "space":
            checked[cursor] = not checked[cursor]
        elif key == "a":
            checked[:] = [True] * len(checked)
        elif key == "n":
            checked[:] = [False] * len(checked)
        elif key == "quit":
            return ScreenResult("quit")
        elif key == "enter":
            selected = tuple(
                choice.id
                for choice, on in zip(choices, checked, strict=True)
                if on
            )
            if selected:
                return ScreenResult("next", selected)
        else:
            continue
        term.paint(_checkbox_lines(choices, checked, cursor))


def _confirm_lines(titles: list[str]) -> list[str]:
    names = ", ".join(titles)
    return [
        bold("Add the Murf docs MCP to these harnesses?"),
        italic(dim("This CLI will write MCP config for the selection below.")),
        "",
        f"  {bold(names)}",
        "",
        _hint(
            ("y", "yes, add"),
            ("n", "back"),
            ("q", "quit"),
        ),
    ]


def confirm_screen(term: Terminal, titles: list[str]) -> ScreenResult:
    term.paint(_confirm_lines(titles))
    while True:
        key = term.read_key()
        if key in {"y", "enter"}:
            return ScreenResult("next")
        if key == "n":
            return ScreenResult("back")
        if key == "quit":
            return ScreenResult("quit")
