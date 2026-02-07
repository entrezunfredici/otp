"""Import command."""
from __future__ import annotations

import argparse
from pathlib import Path

from odoo_task_porter.cli.base_command import BaseCommand, CommandHelper
from odoo_task_porter.cli.generic_functions import build_repository, load_app_config, require_profile
from odoo_task_porter.cli.reporting import emit_report
from odoo_task_porter.services.import_service import ImportOptions, ImportService


class ImportCommand(BaseCommand):
    name = "import"
    summary = "Importer des tâches Markdown vers Odoo."

    def configure(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--profile", required=True)
        parser.add_argument("--project", required=True)
        parser.add_argument("--tasks-md-dir", type=Path)
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--create-only", action="store_true")
        parser.add_argument("--report-json", type=Path)

    def execute(self, args: argparse.Namespace) -> int:
        config = load_app_config(args.config)
        profile = require_profile(config, args.profile)
        repo = build_repository(args.profile, profile)
        tasks_dir = args.tasks_md_dir or config.tasks_md_dir
        options = ImportOptions(dry_run=args.dry_run, create_only=args.create_only)
        report = ImportService(repo).run(tasks_dir, args.project, options)
        emit_report(report, args.report_json)
        return 0

    def helper(self) -> CommandHelper:
        return CommandHelper(
            name=self.name,
            summary=self.summary,
            usage=(
                "odoo-task-porter import --profile <name> --project <project> "
                "[--tasks-md-dir <dir>] [--dry-run] [--create-only] [--report-json <file>]"
            ),
        )
