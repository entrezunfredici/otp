"""Service for importing tasks from Markdown into Odoo."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable

from odoo_task_porter.adapters.markdown import parse_markdown
from odoo_task_porter.adapters.odoo_repo import OdooRepository
from odoo_task_porter.domain.errors import ValidationError
from odoo_task_porter.domain.models import Report
from odoo_task_porter.rules.ids import build_import_key
from odoo_task_porter.transform.mapping import TagMapping, estimation_to_hours


@dataclass
class ImportOptions:
    """Options for import service."""

    dry_run: bool = False
    create_only: bool = False


class ImportService():
    """Import tasks from Markdown into Odoo."""

    def __init__(self, repo: OdooRepository, tag_mapping: TagMapping | None = None) -> None:
        self.repo = repo
        self.tag_mapping = tag_mapping or TagMapping()

    def run(self, tasks_md_dir: Path, project_name: str, options: ImportOptions | None = None) -> Report:
        options = options or ImportOptions()
        report = Report()
        project_id = self.repo.get_project_id(project_name)
        if not options.create_only:
            self.repo.ensure_import_key_field()
        fields = self.repo.fields("project.task", ["planned_hours", "date_deadline", "stage_id", "user_id"])
        planned_hours_field = "planned_hours" if "planned_hours" in fields else None
        deadline_field = "date_deadline" if "date_deadline" in fields else None
        dependency_field = self.repo.supports_dependency_field()
        for path in sorted(tasks_md_dir.glob("*.md")):
            try:
                parsed = parse_markdown(path)
                import_key = build_import_key(project_name, parsed.title)
                values = self._build_values(
                    parsed,
                    project_id,
                    import_key,
                    planned_hours_field,
                    deadline_field,
                    dependency_field,
                )
                action = "update"
                existing = self.repo.find_task_by_import_key(project_id, import_key)
                if not existing:
                    action = "create"
                if options.dry_run:
                    report.add_item(path.name, "dry-run", f"Would {action} task '{parsed.title}'.")
                    continue
                task_id = self.repo.upsert_task(project_id, values, import_key)
                if parsed.dependencies_blocking:
                    self._apply_dependencies(parsed.dependencies_blocking, dependency_field, task_id, report)
                report.add_item(path.name, "ok", f"{action} task '{parsed.title}'.", task_id=task_id)
            except ValidationError as error:
                report.add_item(path.name, "error", str(error))
            except Exception as error:  # noqa: BLE001 - capture to continue
                report.add_item(path.name, "error", str(error))
        return report

    def _build_values(
        self,
        parsed,
        project_id: int,
        import_key: str,
        planned_hours_field: str | None,
        deadline_field: str | None,
        dependency_field: str | None,
    ) -> dict:
        tags = self._tags_for_metadata(parsed.metadata)
        tag_ids = [self.repo.get_or_create_tag(tag) for tag in tags]
        stage_id = self.repo.get_or_create_stage(project_id, parsed.metadata.status)
        description = self._inject_links(parsed.description, parsed.metadata.links)
        if parsed.dependencies_other or (parsed.dependencies_blocking and not dependency_field):
            description = self._append_dependencies(
                description, parsed.dependencies_blocking if not dependency_field else [], parsed.dependencies_other
            )
        values = {
            "name": parsed.title,
            "description": description,
            "project_id": project_id,
            "tag_ids": [(6, 0, tag_ids)],
            "stage_id": stage_id,
            "x_import_key": import_key,
        }
        owner = parsed.metadata.owner
        if owner:
            owner_handle = owner.lstrip("@")
            user_id = self.repo.find_user(owner_handle)
            if user_id:
                values["user_id"] = user_id
        hours = estimation_to_hours(parsed.metadata.estimation)
        if planned_hours_field and hours is not None:
            values[planned_hours_field] = hours
        if deadline_field and parsed.metadata.deadline:
            values[deadline_field] = parsed.metadata.deadline.isoformat()
        return values

    def _tags_for_metadata(self, metadata) -> list[str]:
        tags = [f"{self.tag_mapping.type_prefix}{metadata.task_type}"]
        tags.append(f"{self.tag_mapping.priority_prefix}{metadata.priority}")
        moscow = metadata.moscow.lower().replace("’", "").replace("'", "")
        tags.append(f"{self.tag_mapping.moscow_prefix}{moscow}")
        return tags

    def _inject_links(self, description: str, links: list[str]) -> str:
        if not links:
            return description
        links_section = "Liens:\n" + "\n".join(f"- {link}" for link in links)
        if description:
            return f"{links_section}\n\n{description}"
        return links_section

    def _apply_dependencies(
        self,
        dependencies: Iterable[str],
        field_name: str | None,
        task_id: int,
        report: Report,
    ) -> None:
        dependency_ids: list[int] = []
        for dep in dependencies:
            task_name = self._extract_dependency_title(dep)
            if not task_name:
                continue
            matches = self.repo.find_tasks([["name", "ilike", task_name]], ["id", "name"])
            if matches:
                dependency_ids.append(int(matches[0]["id"]))
        if field_name and dependency_ids:
            self.repo.add_dependencies(task_id, dependency_ids, field_name)
        elif dependency_ids:
            report.add_warning("Dépendances non appliquées: champ manquant dans Odoo.")

    @staticmethod
    def _extract_dependency_title(content: str) -> str | None:
        match = re.search(r"—\s*[“\"]?(.*?)[”\"]?(\s+—|$)", content)
        if match:
            return match.group(1).strip()
        return None

    @staticmethod
    def _append_dependencies(description: str, blocking: Iterable[str], other: Iterable[str]) -> str:
        sections = [description] if description else []
        lines = ["Dépendances:"]
        for dep in blocking:
            lines.append(f"- {dep}")
        for dep in other:
            lines.append(f"- {dep}")
        sections.append("\n".join(lines))
        return "\n\n".join(sections)
