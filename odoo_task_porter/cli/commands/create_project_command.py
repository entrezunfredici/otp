"""Create project command."""
from __future__ import annotations

import argparse
from pathlib import Path

from odoo_task_porter.cli.base_command import BaseCommand, CommandHelper
from odoo_task_porter.cli.generic_functions import build_repository
from odoo_task_porter.cli.inquirer_helper import (
    can_prompt_interactively,
    prompt_select,
    prompt_text,
)
from odoo_task_porter.cli.reporting import emit_report
from odoo_task_porter.services.create_project_service import CreateProjectService


class CreateProjectCommand(BaseCommand):
    name = "create_project"
    summary = "Creer un projet dans Odoo."

    def configure(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--profile")
        parser.add_argument("--project-name")
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
        parser.add_argument("--skip-default-sections", action="store_true")
        parser.add_argument("--skip-default-tasks", action="store_true")
        parser.add_argument("--allow-existing", action="store_true")
        parser.add_argument("--report-json", type=Path)

    def execute(self, args: argparse.Namespace) -> int:
        profile = self._resolve_profile(args)
        project_name = self._resolve_project_name(args)
        repo = build_repository(profile)
        report = CreateProjectService(repo).run(
            project_name,
            templates_source_dir=args.templates_source_dir,
            project_template_file=args.project_template_file,
            with_default_sections=not args.skip_default_sections,
            with_default_tasks=not args.skip_default_tasks,
            allow_existing=args.allow_existing,
        )
        emit_report(report, args.report_json)
        return 0

    def helper(self) -> CommandHelper:
        return CommandHelper(
            name=self.name,
            summary=self.summary,
            usage=(
                "odoo-task-porter create_project [--profile <name>] "
                "[--project-name <name>] [--templates-source-dir <dir>] "
                "[--project-template-file <file>] "
                "[--skip-default-sections] [--skip-default-tasks] "
                "[--allow-existing] [--report-json <file>]"
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

    def _resolve_project_name(self, args: argparse.Namespace) -> str:
        project_name = (args.project_name or "").strip()
        if project_name:
            return project_name
        if not can_prompt_interactively():
            raise ValueError("L'option --project-name est obligatoire hors mode interactif.")
        try:
            project_name = prompt_text("Nom du projet Odoo:")
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "InquirerPy n'est pas installe. Lance 'pip install -e .' puis reessaie."
            ) from exc
        except KeyboardInterrupt as exc:
            raise RuntimeError("Saisie annulee par l'utilisateur.") from exc
        project_name = project_name.strip()
        if not project_name:
            raise ValueError("Le nom du projet ne peut pas etre vide.")
        return project_name
