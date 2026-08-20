RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
REVERSE = "\033[7m"
CYAN = "\033[36m"

# Same number of terminal cells in both states so toggling cannot shift labels.
# Emoji ☑️ is 2 cells; □ is 1 — that mix caused the layout jump.
CHECKED = "[✔]"
UNCHECKED = "[ ]"
POINTER = "❯"


def bold(text: str) -> str:
    return f"{BOLD}{text}{RESET}"


def italic(text: str) -> str:
    return f"{ITALIC}{text}{RESET}"


def dim(text: str) -> str:
    return f"{DIM}{text}{RESET}"


def cyan(text: str) -> str:
    return f"{CYAN}{text}{RESET}"


def keycap(label: str) -> str:
    return f"{REVERSE} {label} {RESET}"
