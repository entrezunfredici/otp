"""CLI commands package."""
from __future__ import annotations

from odoo_task_porter.cli.base_command import BaseCommand
from odoo_task_porter.cli.commands.auth_command import AuthCommand
from odoo_task_porter.cli.commands.config_command import ConfigCommand
from odoo_task_porter.cli.commands.create_project_command import CreateProjectCommand
from odoo_task_porter.cli.commands.export_command import ExportCommand
from odoo_task_porter.cli.commands.help_command import GeneralHelper, HelpCommand
from odoo_task_porter.cli.commands.import_command import ImportCommand
from odoo_task_porter.cli.commands.lint_command import LintCommand


def build_commands() -> list[BaseCommand]:
    """Create command instances and wire the modular help command."""
    commands: list[BaseCommand] = [
        ConfigCommand(),
        AuthCommand(),
        ImportCommand(),
        ExportCommand(),
        LintCommand(),
        CreateProjectCommand(),
    ]
    commands.append(HelpCommand(GeneralHelper(commands)))
    return commands


__all__ = [
    "AuthCommand",
    "BaseCommand",
    "ConfigCommand",
    "CreateProjectCommand",
    "ExportCommand",
    "GeneralHelper",
    "HelpCommand",
    "ImportCommand",
    "LintCommand",
    "build_commands",
]
