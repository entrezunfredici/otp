"""Interactive CLI helpers built on top of InquirerPy."""
from __future__ import annotations

import sys


def can_prompt_interactively() -> bool:
    """Return True when an interactive prompt can be displayed."""
    return sys.stdin.isatty() and sys.stdout.isatty()


def prompt_text(message: str, default: str | None = None) -> str:
    """Prompt for free text using InquirerPy."""
    from InquirerPy import inquirer

    if default is None:
        prompt = inquirer.text(message=message)
    else:
        prompt = inquirer.text(message=message, default=default)
    return str(prompt.execute()).strip()


def prompt_secret(message: str) -> str:
    """Prompt for secret text using InquirerPy."""
    from InquirerPy import inquirer

    prompt = inquirer.secret(message=message)
    return str(prompt.execute()).strip()


def prompt_checkbox(message: str, choices: list[str]) -> list[str]:
    """Prompt for multiple selections using InquirerPy checkbox."""
    from InquirerPy import inquirer

    prompt = inquirer.checkbox(message=message, choices=choices)
    result = prompt.execute()
    return [str(item).strip() for item in result if str(item).strip()]
