"""Project template command."""
from __future__ import annotations

import argparse
from pathlib import Path

from odoo_task_porter.cli.base_command import BaseCommand, CommandHelper
from odoo_task_porter.cli.reporting import emit_report
from odoo_task_porter.services.project_template_service import ProjectTemplateService


class ProjectTemplateCommand(BaseCommand):
    name = "project-template"
    summary = "Creer un dossier projet Odoo depuis un template."

    def configure(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--project-name", required=True)
        parser.add_argument("--output-dir", type=Path, default=Path("projects"))
        parser.add_argument(
            "--templates-source-dir",
            type=Path,
            default=Path("templates/tasks_templates"),
        )
        parser.add_argument(
            "--project-template-file",
            type=Path,
            default=Path("templates/project_template.md"),
        )
        parser.add_argument("--force", action="store_true")
        parser.add_argument("--report-json", type=Path)

    def execute(self, args: argparse.Namespace) -> int:
        report = ProjectTemplateService().run(
            project_name=args.project_name,
            output_dir=args.output_dir,
            templates_source_dir=args.templates_source_dir,
            project_template_file=args.project_template_file,
            force=args.force,
        )
        emit_report(report, args.report_json)
        return 0

    def helper(self) -> CommandHelper:
        return CommandHelper(
            name=self.name,
            summary=self.summary,
            usage=(
                "odoo-task-porter project-template --project-name <name> "
                "[--output-dir <dir>] [--templates-source-dir <dir>] "
                "[--project-template-file <file>] [--force] [--report-json <file>]"
            ),
        )
