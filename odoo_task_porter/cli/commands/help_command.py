"""Help command and modular helper renderer."""
from __future__ import annotations

import argparse

from odoo_task_porter.cli.base_command import BaseCommand, CommandHelper


class GeneralHelper:
    """Render modular CLI help from each command helper."""

    def __init__(self, commands: list[BaseCommand]) -> None:
        self._commands = commands

    def render(self) -> str:
        lines = ["Commandes disponibles:"]
        for command in self._commands:
            helper = command.helper()
            lines.append(f"- {helper.name}: {helper.summary}")
            lines.append(f"  usage: {helper.usage}")
        return "\n".join(lines)


class HelpCommand(BaseCommand):
    name = "help"
    summary = "Afficher l'aide générale modulaire."

    def __init__(self, general_helper: GeneralHelper) -> None:
        self._general_helper = general_helper

    def configure(self, parser: argparse.ArgumentParser) -> None:
        parser.description = "Affiche la liste des commandes et leurs usages."

    def execute(self, args: argparse.Namespace) -> int:
        del args
        print(self._general_helper.render())
        return 0

    def helper(self) -> CommandHelper:
        return CommandHelper(
            name=self.name,
            summary=self.summary,
            usage="odoo-task-porter help",
        )
