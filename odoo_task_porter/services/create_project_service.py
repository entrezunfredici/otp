"""Service for creating projects in Odoo."""
from __future__ import annotations

import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
import re

from odoo_task_porter.adapters.odoo_repo import OdooRepository
from odoo_task_porter.domain.models import Report
from odoo_task_porter.services.import_service import ImportOptions, ImportService

DEFAULT_TASK_TEMPLATE_FILES = [
    "prod_description_project_task.md",
    "prod_analyse_besoin_task.md",
    "prod_problematique_task.md",
    "gov_parties_prenantes_task.md",
    "prod_moscow_fonctionnalites_task.md",
    "prod_personas_user_stories_task.md",
    "prod_decoupage_mvp_versions_task.md",
    "arch_benchmark_architecture_task.md",
    "risk_faisabilite_risques_task.md",
    "research_veille_techno_task.md",
    "prod_estimation_charge_task.md.md",
]

DEFAULT_TASK_DURATIONS_HOURS: dict[str, tuple[float, float]] = {
    "prod_description_project_task.md": (0.5, 1.5),
    "prod_analyse_besoin_task.md": (3.0, 6.0),
    "prod_problematique_task.md": (0.75, 2.0),
    "gov_parties_prenantes_task.md": (1.5, 4.0),
    "prod_moscow_fonctionnalites_task.md": (1.5, 3.0),
    "prod_personas_user_stories_task.md": (6.0, 12.0),
    "prod_decoupage_mvp_versions_task.md": (2.0, 4.0),
    "arch_benchmark_architecture_task.md": (4.0, 8.0),
    "risk_faisabilite_risques_task.md": (4.0, 8.0),
    "research_veille_techno_task.md": (3.0, 6.0),
    "prod_estimation_charge_task.md.md": (3.0, 6.0),
}

DEFAULT_STAGE_NAMES = (
    "templates",
    "cadrage",
    "spécification",
    "en cours",
    "vérification",
    "annulé",
    "demande de modification",
    "validé",
    "ressources",
)
DEFAULT_PROJECT_TEMPLATE_PATH = Path("templates/project_template.md")
DEFAULT_TASK_STAGE_BY_TEMPLATE: dict[str, str] = {
    "prod_description_project_task.md": "cadrage",
    "prod_analyse_besoin_task.md": "cadrage",
    "prod_problematique_task.md": "cadrage",
    "gov_parties_prenantes_task.md": "cadrage",
    "prod_moscow_fonctionnalites_task.md": "cadrage",
    "prod_personas_user_stories_task.md": "cadrage",
    "prod_decoupage_mvp_versions_task.md": "cadrage",
    "arch_benchmark_architecture_task.md": "cadrage",
    "risk_faisabilite_risques_task.md": "cadrage",
    "research_veille_techno_task.md": "cadrage",
    "prod_estimation_charge_task.md.md": "cadrage",
}


class CreateProjectService:
    """Create a project in Odoo when it does not already exist."""

    def __init__(self, repo: OdooRepository) -> None:
        self.repo = repo

    def run(
        self,
        project_name: str,
        templates_source_dir: Path = Path("templates/tasks_templates"),
        project_template_file: Path = DEFAULT_PROJECT_TEMPLATE_PATH,
        with_default_sections: bool = True,
        with_default_tasks: bool = True,
        allow_existing: bool = False,
    ) -> Report:
        name = project_name.strip()
        if not name:
            raise ValueError("Le nom du projet est obligatoire.")

        report = Report()
        existing_id = self.repo.find_project_id(name)
        if existing_id is not None:
            if not allow_existing:
                raise ValueError(f"Le projet '{name}' existe deja (id={existing_id}).")
            project_id = existing_id
            report.add_warning(f"Projet existant reutilise: '{name}' (id={existing_id}).")
        else:
            project_id = self.repo.create_project(name)
            report.add_item(name, "ok", f"Project '{name}' created.", project_id=project_id)

        if with_default_sections:
            for stage_name in DEFAULT_STAGE_NAMES:
                stage_id = self.repo.get_or_create_stage(project_id, stage_name)
                report.add_item(
                    stage_name,
                    "ok",
                    f"Section '{stage_name}' ensured.",
                    stage_id=stage_id,
                )

        if with_default_tasks:
            self._import_default_tasks(
                project_name=name,
                project_id=project_id,
                templates_source_dir=templates_source_dir,
                project_template_file=project_template_file,
                report=report,
            )

        return report

    def _import_default_tasks(
        self,
        project_name: str,
        project_id: int,
        templates_source_dir: Path,
        project_template_file: Path,
        report: Report,
    ) -> None:
        if not templates_source_dir.exists() or not templates_source_dir.is_dir():
            report.add_warning(f"Dossier de templates introuvable: {templates_source_dir}")
            return

        with tempfile.TemporaryDirectory() as temp_dir_str:
            temp_dir = Path(temp_dir_str)
            copied_any = False
            for filename in DEFAULT_TASK_TEMPLATE_FILES:
                source = templates_source_dir / filename
                if not source.exists():
                    report.add_warning(f"Template par defaut absent: {filename}")
                    continue
                destination = temp_dir / filename
                shutil.copy2(source, destination)
                copied_any = True

            if not copied_any:
                report.add_warning("Aucune tache par defaut importee (aucun template trouve).")
                return

            import_report = ImportService(self.repo).run(
                temp_dir,
                project_name,
                ImportOptions(create_only=True),
            )
            stage_mapping = self._load_stage_mapping(project_template_file)
            self._apply_task_stages(import_report, project_id, stage_mapping, report)
            self._apply_default_gantt(import_report, report)
            report.items.extend(import_report.items)
            report.warnings.extend(import_report.warnings)

    def _apply_task_stages(
        self,
        import_report: Report,
        project_id: int,
        stage_mapping: dict[str, str],
        report: Report,
    ) -> None:
        stage_field = self.repo.resolve_task_fields()["stage"]
        task_by_source: dict[str, int] = {}
        for item in import_report.items:
            task_id = item.data.get("task_id")
            if item.status == "ok" and isinstance(task_id, int):
                task_by_source[item.source] = task_id

        for filename in DEFAULT_TASK_TEMPLATE_FILES:
            task_id = task_by_source.get(filename)
            if task_id is None:
                continue
            stage_name = stage_mapping.get(filename)
            if not stage_name:
                continue
            try:
                stage_id = self.repo.get_or_create_stage(project_id, stage_name)
                self.repo.update_task(task_id, {stage_field: stage_id})
                report.add_item(
                    filename,
                    "ok",
                    "Task stage applied from project template.",
                    task_id=task_id,
                    stage=stage_name,
                )
            except Exception as exc:  # noqa: BLE001
                report.add_warning(
                    f"Etape non appliquee sur {filename} (task_id={task_id}): {exc}"
                )

    def _apply_default_gantt(self, import_report: Report, report: Report) -> None:
        (
            start_fields,
            end_fields,
            deadline_field,
            estimation_field,
            field_types,
        ) = self._resolve_schedule_fields()
        if not start_fields or not end_fields:
            raise ValueError(
                "Champs Gantt manquants: impossible de planifier toutes les taches "
                "(start/end introuvables sur project.task)."
            )

        task_by_source: dict[str, int] = {}
        for item in import_report.items:
            task_id = item.data.get("task_id")
            if item.status == "ok" and isinstance(task_id, int):
                task_by_source[item.source] = task_id

        cursor = datetime.now().replace(microsecond=0)
        scheduling_errors: list[str] = []
        for filename in DEFAULT_TASK_TEMPLATE_FILES:
            task_id = task_by_source.get(filename)
            if task_id is None:
                scheduling_errors.append(f"{filename}: tache non creee, planification impossible.")
                continue
            low, high = DEFAULT_TASK_DURATIONS_HOURS.get(filename, (2.0, 4.0))
            duration_hours = (low + high) / 2.0
            start_at = cursor
            end_at = cursor + timedelta(hours=duration_hours)
            if end_at <= start_at:
                end_at = start_at + timedelta(minutes=1)
            start_is_date_like = any(
                self._is_date_like(field_name, field_types.get(field_name))
                for field_name in start_fields
            )
            end_is_date_like = any(
                self._is_date_like(field_name, field_types.get(field_name))
                for field_name in end_fields
            )
            # Some Odoo configs validate planning at date-level; enforce strict next-day end.
            if start_is_date_like or end_is_date_like:
                minimum_end = start_at + timedelta(days=1)
                if end_at < minimum_end:
                    end_at = minimum_end
            values: dict[str, object] = {}
            for start_field in start_fields:
                values[start_field] = self._format_field_value(
                    start_field,
                    start_at,
                    field_types.get(start_field),
                )
            for end_field in end_fields:
                values[end_field] = self._format_field_value(
                    end_field,
                    end_at,
                    field_types.get(end_field),
                )
            if deadline_field:
                values[deadline_field] = end_at.date().isoformat()
            if estimation_field:
                values[estimation_field] = duration_hours
            if not values:
                continue
            try:
                self.repo.update_task(task_id, values)
                report.add_item(
                    filename,
                    "ok",
                    "Gantt schedule applied.",
                    task_id=task_id,
                    start=values.get(start_fields[0]) if start_fields else None,
                    end=values.get(end_fields[0]) if end_fields else None,
                    duration_hours=duration_hours,
                )
            except Exception as exc:  # noqa: BLE001 - keep bootstrap resilient
                # Retry once with a wider gap to satisfy strict date constraints.
                retry_end = start_at + timedelta(days=2)
                retry_values = dict(values)
                for end_field in end_fields:
                    retry_values[end_field] = self._format_field_value(
                        end_field,
                        retry_end,
                        field_types.get(end_field),
                    )
                if deadline_field:
                    retry_values[deadline_field] = retry_end.date().isoformat()
                try:
                    self.repo.update_task(task_id, retry_values)
                    report.add_item(
                        filename,
                        "ok",
                        "Gantt schedule applied (retry).",
                        task_id=task_id,
                        start=retry_values.get(start_fields[0]) if start_fields else None,
                        end=retry_values.get(end_fields[0]) if end_fields else None,
                        duration_hours=duration_hours,
                    )
                except Exception as retry_exc:  # noqa: BLE001
                    scheduling_errors.append(
                        f"{filename} (task_id={task_id}): {retry_exc}"
                    )
            cursor = end_at

        if scheduling_errors:
            message = "Echec de planification Gantt (start/end requis) sur:\n- " + "\n- ".join(
                scheduling_errors
            )
            raise RuntimeError(message)

    def _resolve_schedule_fields(
        self,
    ) -> tuple[list[str], list[str], str | None, str | None, dict[str, str]]:
        spec = self.repo.get_version_spec()
        all_fields = self.repo.fields(spec.models.task, [])
        available = set(all_fields.keys())

        def pick_all(candidates: list[str]) -> list[str]:
            return [name for name in candidates if name in available]

        # Different Odoo editions/modules expose different planning field names.
        start_fields = pick_all(["date_start", "planned_date_begin", "date_assigning"])
        end_fields = pick_all(["date_end", "planned_date_end"])
        deadline_candidates = pick_all(["date_deadline"])
        estimation_candidates = pick_all(["planned_hours", "allocated_hours"])
        deadline_field = deadline_candidates[0] if deadline_candidates else None
        estimation_field = estimation_candidates[0] if estimation_candidates else None
        field_types: dict[str, str] = {}
        for field_name in [*start_fields, *end_fields, deadline_field, estimation_field]:
            if field_name:
                metadata = all_fields.get(field_name) or {}
                field_type = str(metadata.get("type") or "").strip()
                if field_type:
                    field_types[field_name] = field_type
        return start_fields, end_fields, deadline_field, estimation_field, field_types

    @staticmethod
    def _format_field_value(field_name: str, value: datetime, field_type: str | None = None) -> str:
        if field_type == "date" or field_name in {"date_assigning", "date_deadline"}:
            return value.date().isoformat()
        return value.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _is_date_like(field_name: str | None, field_type: str | None) -> bool:
        if not field_name:
            return False
        if field_type == "date":
            return True
        return field_name in {"date_assigning", "date_deadline"}

    def _load_stage_mapping(self, project_template_file: Path) -> dict[str, str]:
        mapping = dict(DEFAULT_TASK_STAGE_BY_TEMPLATE)
        if not project_template_file.exists() or not project_template_file.is_file():
            return mapping
        content = project_template_file.read_text(encoding="utf-8")
        parsed = self._parse_stage_mapping(content)
        if parsed:
            mapping.update(parsed)
        return mapping

    @staticmethod
    def _parse_stage_mapping(template_content: str) -> dict[str, str]:
        lines = template_content.splitlines()
        mapping: dict[str, str] = {}
        in_section = False
        for raw_line in lines:
            line = raw_line.strip()
            if line.lower().startswith("## etapes des taches"):
                in_section = True
                continue
            if in_section and line.startswith("## "):
                break
            if not in_section:
                continue
            match = re.match(r"^-\s*([^\s:]+\.md(?:\.md)?)\s*:\s*(.+)$", line)
            if not match:
                continue
            filename = match.group(1).strip()
            stage_name = match.group(2).strip()
            if filename and stage_name:
                mapping[filename] = stage_name
        return mapping
