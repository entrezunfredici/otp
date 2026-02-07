"""Lint command."""
from __future__ import annotations

import argparse
from pathlib import Path

from odoo_task_porter.cli.base_command import BaseCommand, CommandHelper
from odoo_task_porter.cli.generic_functions import load_app_config
from odoo_task_porter.cli.reporting import emit_report
from odoo_task_porter.services.lint_service import LintService


class LintCommand(BaseCommand):
    name = "lint"
    summary = "Valider les fichiers Markdown."

    def configure(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--tasks-md-dir", type=Path)
        parser.add_argument("--report-json", type=Path)

    def execute(self, args: argparse.Namespace) -> int:
        config = load_app_config(args.config)
        tasks_dir = args.tasks_md_dir or config.tasks_md_dir
        report = LintService().run(tasks_dir)
        emit_report(report, args.report_json)
        return 0

    def helper(self) -> CommandHelper:
        return CommandHelper(
            name=self.name,
            summary=self.summary,
            usage="odoo-task-porter lint [--tasks-md-dir <dir>] [--report-json <file>]",
        )
