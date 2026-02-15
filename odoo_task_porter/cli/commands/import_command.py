"""Import command."""
from __future__ import annotations

import argparse
from pathlib import Path

from odoo_task_porter.cli.base_command import BaseCommand, CommandHelper
from odoo_task_porter.cli.generic_functions import build_repository, load_app_config
from odoo_task_porter.cli.inquirer_helper import can_prompt_interactively, prompt_select, prompt_text
from odoo_task_porter.cli.reporting import emit_report
from odoo_task_porter.services.import_service import ImportOptions, ImportService


class ImportCommand(BaseCommand):
    name = "import"
    summary = "Importer des taches Markdown vers Odoo."

    def configure(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--profile")
        parser.add_argument("--project")
        parser.add_argument("--tasks-md-dir", type=Path)
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--create-only", action="store_true")
        parser.add_argument("--report-json", type=Path)

    def execute(self, args: argparse.Namespace) -> int:
        config = load_app_config(args.config)
        profile = self._resolve_profile(args)
        repo = build_repository(profile)
        project = self._resolve_project(args, repo)
        tasks_dir = self._resolve_tasks_dir(args, config.tasks_md_dir)
        options = ImportOptions(dry_run=args.dry_run, create_only=args.create_only)
        report = ImportService(repo).run(tasks_dir, project, options)
        emit_report(report, args.report_json)
        return 0

    def helper(self) -> CommandHelper:
        return CommandHelper(
            name=self.name,
            summary=self.summary,
            usage=(
                "odoo-task-porter import [--profile <name>] [--project <project>] "
                "[--tasks-md-dir <dir>] [--dry-run] [--create-only] [--report-json <file>]"
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

    def _resolve_tasks_dir(self, args: argparse.Namespace, default_tasks_dir: Path) -> Path:
        if args.tasks_md_dir:
            tasks_dir = args.tasks_md_dir
        elif can_prompt_interactively():
            try:
                selected = prompt_text(
                    "Saisis le dossier des taches Markdown a importer:",
                    default=str(default_tasks_dir),
                )
            except ModuleNotFoundError as exc:
                raise RuntimeError(
                    "InquirerPy n'est pas installe. Lance 'pip install -e .' puis reessaie."
                ) from exc
            except KeyboardInterrupt as exc:
                raise RuntimeError("Saisie annulee par l'utilisateur.") from exc
            if not selected:
                raise ValueError("Aucun dossier selectionne.")
            tasks_dir = Path(selected)
        else:
            tasks_dir = default_tasks_dir

        tasks_dir = tasks_dir.expanduser()
        if not tasks_dir.exists():
            raise ValueError(f"Dossier introuvable: {tasks_dir}")
        if not tasks_dir.is_dir():
            raise ValueError(f"Le chemin n'est pas un dossier: {tasks_dir}")
        return tasks_dir
