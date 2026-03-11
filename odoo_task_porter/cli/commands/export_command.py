"""Export command."""
from __future__ import annotations

import argparse
from pathlib import Path

from odoo_task_porter.cli.base_command import BaseCommand, CommandHelper
from odoo_task_porter.cli.generic_functions import (
    build_repository,
    load_app_config,
    with_progress_bar,
)
from odoo_task_porter.cli.inquirer_helper import can_prompt_interactively, prompt_select
from odoo_task_porter.cli.reporting import emit_report
from odoo_task_porter.services.export_service import ExportOptions, ExportService


class ExportCommand(BaseCommand):
    name = "export"
    summary = "Exporter des taches Odoo vers Markdown."

    def configure(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--profile")
        parser.add_argument("--project")
        parser.add_argument("--templates-empty-dir", type=Path)
        parser.add_argument("--export-out-dir", type=Path)
        parser.add_argument("--stage")
        parser.add_argument("--tag")
        parser.add_argument("--domain")
        parser.add_argument("--report-json", type=Path)

    def execute(self, args: argparse.Namespace) -> int:
        config = load_app_config(args.config)
        profile = self._resolve_profile(args)
        repo = build_repository(profile)
        project = self._resolve_project(args, repo)
        export_dir = args.export_out_dir or config.export_out_dir
        templates_dir = args.templates_empty_dir or config.templates_empty_dir
        options = ExportOptions(stage=args.stage, tag=args.tag, domain=args.domain)
        service = ExportService(repo)
        report = None
        observed_total = 0

        def action(progress, task_id):
            nonlocal report, observed_total

            def on_progress(done: int, total: int) -> None:
                nonlocal observed_total
                observed_total = total
                normalized_total = max(total, 1)
                normalized_done = min(max(done, 0), normalized_total)
                progress.update(task_id, total=normalized_total, completed=normalized_done)

            report = service.run(
                export_dir,
                project,
                templates_dir,
                options,
                on_progress=on_progress,
            )
            final_total = max(observed_total, 1)
            progress.update(task_id, total=final_total, completed=final_total)

        with_progress_bar("Export des taches", 1, action)
        if report is None:
            raise RuntimeError("Le rapport d'export n'a pas ete genere.")
        emit_report(report, args.report_json)
        return 0

    def helper(self) -> CommandHelper:
        return CommandHelper(
            name=self.name,
            summary=self.summary,
            usage=(
                "odoo-task-porter export [--profile <name>] [--project <project>] "
                "[--templates-empty-dir <dir>] [--export-out-dir <dir>] "
                "[--stage <name>] [--tag <tag>] [--domain <domain>] [--report-json <file>]"
            ),
        )

    def _resolve_profile(self, args: argparse.Namespace) -> str:
        profile = (args.profile or "").strip()
        if profile:
            return profile
        if not can_prompt_interactively():
            raise ValueError("L'option --profile est obligatoire hors mode interactif.")

        from odoo_task_porter.config.auth import AuthManager

        profiles = AuthManager().list_profiles()
        if not profiles:
            raise ValueError(
                "Aucun profil disponible. Lance d'abord 'odoo-task-porter auth set --profile <name>'."
            )
        try:
            selected = prompt_select("Selectionne un profil Odoo:", profiles)
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "InquirerPy n'est pas installe. Lance 'pip install -e .' puis reessaie."
            ) from exc
        except KeyboardInterrupt as exc:
            raise RuntimeError("Saisie annulee par l'utilisateur.") from exc
        if not selected:
            raise ValueError("Aucun profil selectionne.")
        return selected

    def _resolve_project(self, args: argparse.Namespace, repo) -> str:
        project = (args.project or "").strip()
        if project:
            return project
        if not can_prompt_interactively():
            raise ValueError("L'option --project est obligatoire hors mode interactif.")

        projects = repo.list_project_names()
        if not projects:
            raise ValueError("Aucun projet Odoo disponible pour ce profil.")
        try:
            selected = prompt_select("Selectionne un projet Odoo:", projects)
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "InquirerPy n'est pas installe. Lance 'pip install -e .' puis reessaie."
            ) from exc
        except KeyboardInterrupt as exc:
            raise RuntimeError("Saisie annulee par l'utilisateur.") from exc
        if not selected:
            raise ValueError("Aucun projet selectionne.")
        return selected
