"""Command-line entrypoint for odoo-task-porter."""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

from odoo_task_porter.cli.base_command import BaseCommand
from odoo_task_porter.cli.commands import GeneralHelper, build_commands
from odoo_task_porter.domain.errors import PorterError


def build_parser(commands: list[BaseCommand]) -> argparse.ArgumentParser:
    """Build the root parser and register all command classes."""
    parser = argparse.ArgumentParser(
        prog="odoo-task-porter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--log-level", default="INFO")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command in commands:
        command.register(subparsers)

    parser.epilog = GeneralHelper(commands).render()
    return parser


def main() -> int:
    """CLI main entrypoint."""
    commands = build_commands()
    parser = build_parser(commands)
    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    if args.config is None:
        from odoo_task_porter.config.settings import DEFAULT_CONFIG_PATH

        args.config = DEFAULT_CONFIG_PATH

    try:
        return args._handler(args)
    except (RuntimeError, ValueError, PorterError) as exc:
        print(str(exc))
        return 2


__all__ = ["build_parser", "main"]
