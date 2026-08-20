from __future__ import annotations

from murf_mcp.setup_docs_mcp.tui.screens import Choice, checkbox_screen, confirm_screen
from murf_mcp.setup_docs_mcp.tui.terminal import Terminal

_SELECT = "select"
_CONFIRM = "confirm"


def run_detected_wizard(choices: list[Choice]) -> list[str] | None:
    """
    Checkbox → confirm. n on confirm returns to the checkbox.

    Returns selected ids, or None if the user quit.
    """
    if not choices:
        return []

    checked = [True] * len(choices)
    selected: tuple[str, ...] = ()
    screen = _SELECT

    with Terminal() as term:
        while True:
            if screen == _SELECT:
                result = checkbox_screen(term, choices, checked)
                if result.action == "quit":
                    return None
                selected = result.selected
                screen = _CONFIRM
                continue

            titles = [choice.title for choice in choices if choice.id in selected]
            result = confirm_screen(term, titles)
            if result.action == "next":
                return list(selected)
            if result.action == "back":
                screen = _SELECT
                continue
            return None
