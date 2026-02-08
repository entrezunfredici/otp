"""Export command."""
from __future__ import annotations

import argparse
from pathlib import Path

from odoo_task_porter.cli.base_command import BaseCommand, CommandHelper
from odoo_task_porter.cli.generic_functions import build_repository, load_app_config
from odoo_task_porter.cli.reporting import emit_report
from odoo_task_porter.services.export_service import ExportOptions, ExportService


class ExportCommand(BaseCommand):
    name = "export"
    summary = "Exporter des tâches Odoo vers Markdown."

    def configure(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--profile", required=True)
        parser.add_argument("--project", required=True)
        parser.add_argument("--templates-empty-dir", type=Path)
        parser.add_argument("--export-out-dir", type=Path)
        parser.add_argument("--stage")
        parser.add_argument("--tag")
        parser.add_argument("--domain")
        parser.add_argument("--report-json", type=Path)

    def execute(self, args: argparse.Namespace) -> int:
        config = load_app_config(args.config)
        repo = build_repository(args.profile)
        export_dir = args.export_out_dir or config.export_out_dir
        templates_dir = args.templates_empty_dir or config.templates_empty_dir
        options = ExportOptions(stage=args.stage, tag=args.tag, domain=args.domain)
        report = ExportService(repo).run(export_dir, args.project, templates_dir, options)
        emit_report(report, args.report_json)
        return 0

    def helper(self) -> CommandHelper:
        return CommandHelper(
            name=self.name,
            summary=self.summary,
            usage=(
                "odoo-task-porter export --profile <name> --project <project> "
                "[--templates-empty-dir <dir>] [--export-out-dir <dir>] "
                "[--stage <name>] [--tag <tag>] [--domain <domain>] [--report-json <file>]"
            ),
        )
