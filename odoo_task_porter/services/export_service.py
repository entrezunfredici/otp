"""Service for exporting tasks from Odoo to Markdown."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
import ast
import re

from odoo_task_porter.adapters.markdown import load_template, render_markdown
from odoo_task_porter.adapters.odoo_repo import OdooRepository
from odoo_task_porter.domain.models import Report, TaskMetadata
from odoo_task_porter.rules.normalize import slugify
from odoo_task_porter.transform.mapping import STAGE_TO_STATUS, hours_to_estimation


@dataclass
class ExportOptions:
    """Options for export service."""

    stage: str | None = None
    tag: str | None = None
    domain: str | None = None


ProgressCallback = Callable[[int, int], None]


class ExportService:
    """Export tasks from Odoo into Markdown."""

    def __init__(self, repo: OdooRepository) -> None:
        self.repo = repo

    def run(
        self,
        export_out_dir: Path,
        project_name: str,
        templates_empty_dir: Path,
        options: ExportOptions | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> Report:
        options = options or ExportOptions()
        report = Report()
        version = self.repo.get_server_major_version()
        spec = self.repo.get_version_spec()
        if version in (18, 19):
            report.add_warning(f"Odoo version detectee: v{version}. Mapping: {spec.version_name}.")
        elif version is not None:
            report.add_warning(
                f"Odoo version detectee: v{version}. Fallback mapping: {spec.version_name}."
            )
        else:
            report.add_warning(
                f"Version Odoo non detectee. Fallback mapping: {spec.version_name}."
            )
        export_out_dir.mkdir(parents=True, exist_ok=True)
        project_id = self.repo.get_project_id(project_name)
        task_fields = self.repo.resolve_task_fields()
        domain = [[task_fields["project"], "=", project_id]]
        if options.stage:
            domain.append([f"{task_fields['stage']}.name", "=", options.stage])
        if options.tag:
            tag_id = self._find_tag_id(options.tag)
            if tag_id:
                domain.append([task_fields["tags"], "in", [tag_id]])
        if options.domain:
            domain.extend(self._parse_domain(options.domain))
        estimation_field = task_fields["estimation_hours"]
        import_key_field = task_fields["import_key"]
        owner_field = task_fields["owner"]
        fields = [
            task_fields["id"],
            task_fields["name"],
            task_fields["description"],
            task_fields["tags"],
            task_fields["stage"],
        ]
        deadline_field = task_fields["deadline"]
        if deadline_field:
            fields.append(deadline_field)
        if estimation_field:
            fields.append(estimation_field)
        if import_key_field:
            fields.append(import_key_field)
        if owner_field:
            fields.append(owner_field)
        if estimation_field is None:
            report.add_warning(
                "Aucun champ d'estimation supporte detecte (planned_hours/allocated_hours)."
            )
        if import_key_field is None:
            report.add_warning(
                "Champ x_import_key indisponible: fallback sur l'ID interne pour nommer les fichiers."
            )
        if deadline_field is None:
            report.add_warning("Champ de deadline indisponible (date_deadline).")
        if owner_field is None:
            report.add_warning("Aucun champ d'assignation detecte (user_id/user_ids).")
        tasks = self.repo.find_tasks(domain, fields)
        total_tasks = len(tasks)
        if on_progress is not None:
            on_progress(0, total_tasks)
        for index, task in enumerate(tasks, start=1):
            try:
                metadata = self._build_metadata(task, task_fields, estimation_field, owner_field)
                template_path = self._select_template(templates_empty_dir, metadata.task_type)
                template = load_template(template_path)
                content = render_markdown(
                    template,
                    str(task[task_fields["name"]]),
                    metadata,
                    self._body_from_description(task, task_fields["description"]),
                )
                import_key = (task.get(import_key_field) if import_key_field else None) or str(
                    task[task_fields["id"]]
                )
                filename = (
                    f"{metadata.task_type}_{slugify(str(task[task_fields['name']]))}__{import_key}.md"
                )
                out_path = export_out_dir / filename
                out_path.write_text(content, encoding="utf-8")
                report.add_item(
                    str(out_path),
                    "ok",
                    f"Exported task '{str(task[task_fields['name']])}'.",
                )
            finally:
                if on_progress is not None:
                    on_progress(index, total_tasks)
        return report

    def _find_tag_id(self, tag_name: str) -> int | None:
        return self.repo.find_tag_id(tag_name)

    def _build_metadata(
        self,
        task: dict,
        task_fields: dict[str, str | None],
        estimation_field: str | None,
        owner_field: str | None,
    ) -> TaskMetadata:
        tag_names = self.repo.read_project_tags(task.get(task_fields["tags"], []))
        task_type = self._extract_tag_value(tag_names, "type_") or "dev"
        priority = self._extract_tag_value(tag_names, "priority_") or "P2"
        moscow_raw = self._extract_tag_value(tag_names, "moscow_") or "must"
        moscow = self._normalize_moscow(moscow_raw)
        status = STAGE_TO_STATUS.get(task.get(task_fields["stage"], [None, ""])[1], "todo")
        estimation_hours = task.get(estimation_field) if estimation_field else None
        estimation = hours_to_estimation(estimation_hours)
        owner = self._format_owner(task, owner_field)
        deadline = self._parse_deadline(task.get(task_fields["deadline"]) if task_fields["deadline"] else None)
        links = self._extract_links(str(task.get(task_fields["description"]) or ""))
        return TaskMetadata(
            task_type=task_type,
            status=status,
            priority=priority,
            moscow=moscow,
            estimation=estimation,
            owner=owner,
            deadline=deadline,
            links=links,
        )

    def _select_template(self, templates_empty_dir: Path, task_type: str) -> Path:
        candidate = templates_empty_dir / f"{task_type}.md"
        if candidate.exists():
            return candidate
        fallback = templates_empty_dir / "dev.md"
        return fallback

    @staticmethod
    def _extract_tag_value(tags: list[str], prefix: str) -> str | None:
        for tag in tags:
            if tag.startswith(prefix):
                return tag[len(prefix) :]
        return None

    @staticmethod
    def _normalize_moscow(value: str) -> str:
        mapping = {"must": "Must", "should": "Should", "could": "Could", "wont": "Won't"}
        return mapping.get(value.lower(), "Must")

    def _format_owner(self, task: dict, owner_field: str | None) -> str | None:
        if not owner_field:
            return None
        user_field = task.get(owner_field)
        if not user_field:
            return None
        if owner_field == "user_id":
            if isinstance(user_field, list) and len(user_field) > 1:
                return f"@{user_field[1]}"
            return f"@{user_field}"
        if owner_field == "user_ids" and isinstance(user_field, list):
            user_ids = [int(value) for value in user_field if isinstance(value, int)]
            names = self.repo.read_user_names(user_ids)
            if names:
                return f"@{names[0]}"
        return None

    @staticmethod
    def _parse_deadline(value) -> date | None:
        if not value:
            return None
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return None
            try:
                return date.fromisoformat(raw)
            except ValueError:
                # Odoo can return datetime strings like "YYYY-MM-DD HH:MM:SS".
                normalized = raw.replace("Z", "+00:00")
                return datetime.fromisoformat(normalized).date()
        return None

    @staticmethod
    def _extract_links(description: str) -> list[str]:
        match = re.search(r"^Liens:\s*(?:\n|- )(.*?)(?:\n\n|$)", description, re.S | re.M)
        if not match:
            return []
        block = match.group(1)
        return [line.strip("- ") for line in block.splitlines() if line.strip()]

    @staticmethod
    def _body_from_description(task: dict, description_field: str | None) -> str:
        description = str(task.get(description_field) or "") if description_field else ""
        if description.startswith("Liens:"):
            parts = description.split("\n\n", 1)
            if len(parts) > 1:
                return parts[1]
            return ""
        return description

    @staticmethod
    def _parse_domain(raw_domain: str) -> list:
        try:
            value = ast.literal_eval(raw_domain)
        except (SyntaxError, ValueError) as error:
            raise ValueError(f"Invalid domain: {raw_domain}") from error
        if not isinstance(value, list):
            raise ValueError("Domain must be a list.")
        return value
