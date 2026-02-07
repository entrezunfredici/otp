"""Interactive CLI helpers built on top of InquirerPy."""
from __future__ import annotations

import sys


def can_prompt_interactively() -> bool:
    """Return True when an interactive prompt can be displayed."""
    return sys.stdin.isatty() and sys.stdout.isatty()


def prompt_text(message: str, default: str | None = None) -> str:
    """Prompt for free text using InquirerPy."""
    from InquirerPy import inquirer

    prompt = inquirer.text(message=message, default=default)
    return str(prompt.execute()).strip()
