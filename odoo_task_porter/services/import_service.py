"""Service for importing tasks from Markdown into Odoo."""
from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
import re
from typing import Iterable

from odoo_task_porter.adapters.markdown import (
    html_to_odoo_html,
    is_odoo_html_fragment,
    markdown_to_odoo_html,
    parse_markdown,
)
from odoo_task_porter.adapters.odoo_repo import OdooRepository
from odoo_task_porter.domain.errors import ValidationError
from odoo_task_porter.domain.models import ParsedMarkdown, Report
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

        project_id = self.repo.get_project_id(project_name)
        task_fields = self.repo.resolve_task_fields()
        import_key_field = task_fields["import_key"]
        if not options.create_only:
            if import_key_field:
                self.repo.ensure_import_key_field(import_key_field)
            else:
                report.add_warning(
                    "Champ x_import_key indisponible: fallback sur le titre pour detecter les mises a jour."
                )

        estimation_field = task_fields["estimation_hours"]
        deadline_field = task_fields["deadline"]
        owner_field = task_fields["owner"]
        if estimation_field is None:
            report.add_warning(
                "Aucun champ d'estimation supporte detecte (planned_hours/allocated_hours)."
            )
        if owner_field is None:
            report.add_warning("Aucun champ d'assignation detecte (user_id/user_ids).")

        dependency_field = self.repo.supports_dependency_field()
        imported_tasks: list[tuple[ParsedMarkdown, int]] = []
        code_to_task_id: dict[str, int] = {}

        for path in sorted(tasks_md_dir.glob("*.md")):
            try:
                parsed = parse_markdown(path)
                task_title, used_fallback_title = self._resolve_task_title(parsed)
                if used_fallback_title:
                    report.add_warning(
                        f"{path.name}: titre generique detecte, titre importe: '{task_title}'."
                    )
                import_key = build_import_key(project_name, task_title)
                values = self._build_values(
                    parsed,
                    task_title,
                    project_id,
                    import_key,
                    task_fields,
                    estimation_field,
                    deadline_field,
                    owner_field,
                    dependency_field,
                )

                action = "update"
                if import_key_field:
                    existing = self.repo.find_task_by_import_key(project_id, import_key)
                else:
                    existing = self.repo.find_task_by_project_and_name(project_id, task_title)
                if not existing:
                    action = "create"

                if options.dry_run:
                    report.add_item(path.name, "dry-run", f"Would {action} task '{task_title}'.")
                    continue

                task_id = self.repo.upsert_task(project_id, values, import_key)
                imported_tasks.append((parsed, task_id))
                if parsed.task_code:
                    code_to_task_id[parsed.task_code] = task_id
                report.add_item(path.name, "ok", f"{action} task '{task_title}'.", task_id=task_id)
            except ValidationError as error:
                report.add_item(path.name, "error", str(error))
            except Exception as error:  # noqa: BLE001 - capture to continue
                report.add_item(path.name, "error", str(error))

        if not options.dry_run and dependency_field:
            for parsed, task_id in imported_tasks:
                if not parsed.dependencies_blocking:
                    continue
                self._apply_dependencies(
                    dependencies=parsed.dependencies_blocking,
                    field_name=dependency_field,
                    task_id=task_id,
                    report=report,
                    task_name_field=task_fields["name"],
                    task_project_field=task_fields["project"],
                    project_id=project_id,
                    code_to_task_id=code_to_task_id,
                    source_name=parsed.source_path.name,
                )

        return report

    def _build_values(
        self,
        parsed: ParsedMarkdown,
        task_title: str,
        project_id: int,
        import_key: str,
        task_fields: dict[str, str | None],
        estimation_field: str | None,
        deadline_field: str | None,
        owner_field: str | None,
        dependency_field: str | None,
    ) -> dict:
        tags = self._tags_for_metadata(parsed.metadata)
        tag_ids = [self.repo.get_or_create_tag(tag) for tag in tags]
        stage_id = self.repo.get_or_create_stage(project_id, parsed.metadata.status)

        html_description = self._extract_html_description_body(parsed.description)
        if html_description is not None and is_odoo_html_fragment(html_description):
            description_html = self._inject_links_html(html_description, parsed.metadata.links)
            if parsed.dependencies_other or (parsed.dependencies_blocking and not dependency_field):
                description_html = self._append_dependencies_html(
                    description_html,
                    parsed.dependencies_blocking if not dependency_field else [],
                    parsed.dependencies_other,
                )
            description = html_to_odoo_html(description_html)
        else:
            description_markdown = self._inject_links(parsed.description, parsed.metadata.links)
            if parsed.dependencies_other or (parsed.dependencies_blocking and not dependency_field):
                description_markdown = self._append_dependencies(
                    description_markdown,
                    parsed.dependencies_blocking if not dependency_field else [],
                    parsed.dependencies_other,
                )
            description = markdown_to_odoo_html(description_markdown)

        values = {
            task_fields["name"]: task_title,
            task_fields["description"]: description,
            task_fields["project"]: project_id,
            task_fields["tags"]: [(6, 0, tag_ids)],
            task_fields["stage"]: stage_id,
        }
        if task_fields["import_key"]:
            values[task_fields["import_key"]] = import_key

        owner = parsed.metadata.owner
        if owner:
            owner_handle = owner.lstrip("@")
            user_id = self.repo.find_user(owner_handle)
            if user_id and owner_field == "user_id":
                values["user_id"] = user_id
            elif user_id and owner_field == "user_ids":
                values["user_ids"] = [(6, 0, [user_id])]

        hours = estimation_to_hours(parsed.metadata.estimation)
        if estimation_field and hours is not None:
            values[estimation_field] = hours
        if deadline_field and parsed.metadata.deadline:
            values[deadline_field] = parsed.metadata.deadline.isoformat()

        return values

    @staticmethod
    def _resolve_task_title(parsed: ParsedMarkdown) -> tuple[str, bool]:
        title = parsed.title.strip()
        if not ImportService._is_placeholder_title(title):
            return title, False

        source_slug = ImportService._source_slug(parsed.source_path)
        if parsed.task_code and source_slug:
            return f"{parsed.task_code} - {source_slug}", True
        if parsed.task_code:
            return f"{parsed.task_code} - task", True
        if source_slug:
            return source_slug, True
        return title, False

    @staticmethod
    def _is_placeholder_title(title: str) -> bool:
        normalized = title.strip().lower()
        return normalized.startswith("[titre]") or normalized.startswith("[title]")

    @staticmethod
    def _source_slug(source_path: Path) -> str:
        stem = source_path.stem
        if "__" in stem:
            _, slug = stem.split("__", 1)
        else:
            slug = stem
        slug = slug.replace("_", " ").replace("-", " ")
        return re.sub(r"\s+", " ", slug).strip()

    def _tags_for_metadata(self, metadata) -> list[str]:
        tags = [f"{self.tag_mapping.type_prefix}{metadata.task_type}"]
        tags.append(f"{self.tag_mapping.priority_prefix}{metadata.priority}")
        moscow = metadata.moscow.lower().replace("'", "")
        tags.append(f"{self.tag_mapping.moscow_prefix}{moscow}")
        return tags

    def _inject_links(self, description: str, links: list[str]) -> str:
        if not links:
            return description
        links_section = "Liens:\n" + "\n".join(f"- {link}" for link in links)
        if description:
            return f"{links_section}\n\n{description}"
        return links_section

    def _inject_links_html(self, description: str, links: list[str]) -> str:
        if not links:
            return description
        links_items = "".join(f"<li>{escape(link)}</li>" for link in links)
        links_section = f"<p>Liens:</p><ul>{links_items}</ul>"
        if description:
            return f"{links_section}\n{description}"
        return links_section

    def _apply_dependencies(
        self,
        dependencies: Iterable[str],
        field_name: str | None,
        task_id: int,
        report: Report,
        task_name_field: str | None,
        task_project_field: str | None,
        project_id: int,
        code_to_task_id: dict[str, int],
        source_name: str,
    ) -> None:
        dependency_ids: list[int] = []
        unresolved: list[str] = []
        resolved_fields = self.repo.resolve_task_fields()
        task_id_field = resolved_fields["id"]

        for dep in dependencies:
            dependency_code = self._extract_dependency_code(dep)
            if not dependency_code:
                unresolved.append(dep)
                continue

            imported_dependency_id = code_to_task_id.get(dependency_code)
            if imported_dependency_id:
                if imported_dependency_id != task_id:
                    dependency_ids.append(imported_dependency_id)
                continue

            if not task_name_field or not task_project_field:
                unresolved.append(dep)
                continue

            matches = self.repo.find_tasks(
                [
                    [task_project_field, "=", project_id],
                    [task_name_field, "ilike", dependency_code],
                ],
                [task_id_field, task_name_field],
            )
            if matches:
                dependency_ids.append(int(matches[0][task_id_field]))
            else:
                unresolved.append(dep)

        dependency_ids = sorted(set(dep_id for dep_id in dependency_ids if dep_id != task_id))
        if field_name and dependency_ids:
            self.repo.add_dependencies(task_id, dependency_ids, field_name)
        elif dependency_ids:
            report.add_warning("Dependances non appliquees: champ manquant dans Odoo.")

        if unresolved:
            report.add_warning(
                f"{source_name}: dependances introuvables ou invalides: {', '.join(unresolved)}"
            )

    @staticmethod
    def _extract_dependency_code(content: str) -> str | None:
        match = re.search(r"^\s*\((?:Bloquante|Non-bloquante)\)\s*([A-Za-z]+-\d+)\b", content)
        if not match:
            match = re.search(r"\b([A-Za-z]+-\d+)\b", content)
        if match:
            return match.group(1).upper()
        return None

    @staticmethod
    def _append_dependencies(description: str, blocking: Iterable[str], other: Iterable[str]) -> str:
        sections = [description] if description else []
        lines = ["Dependances:"]
        for dep in blocking:
            lines.append(f"- {dep}")
        for dep in other:
            lines.append(f"- {dep}")
        sections.append("\n".join(lines))
        return "\n\n".join(sections)

    @staticmethod
    def _append_dependencies_html(description: str, blocking: Iterable[str], other: Iterable[str]) -> str:
        sections = [description] if description else []
        deps = [*blocking, *other]
        if deps:
            items = "".join(f"<li>{escape(dep)}</li>" for dep in deps)
            sections.append(f"<p>Dependances:</p><ul>{items}</ul>")
        return "\n".join(sections)

    @staticmethod
    def _extract_html_description_body(description: str) -> str | None:
        lines = description.splitlines()
        index = 0
        while index < len(lines) and not lines[index].strip():
            index += 1

        if index < len(lines) and re.match(r"^##\s+description\b", lines[index].strip(), re.I):
            index += 1
            while index < len(lines) and not lines[index].strip():
                index += 1

        if index >= len(lines):
            return None
        return "\n".join(lines[index:]).strip()
