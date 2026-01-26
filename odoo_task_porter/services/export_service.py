"""Service for exporting tasks from Odoo to Markdown."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
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
    ) -> Report:
        options = options or ExportOptions()
        report = Report()
        export_out_dir.mkdir(parents=True, exist_ok=True)
        project_id = self.repo.get_project_id(project_name)
        domain = [["project_id", "=", project_id]]
        if options.stage:
            domain.append(["stage_id.name", "=", options.stage])
        if options.tag:
            tag_id = self._find_tag_id(options.tag)
            if tag_id:
                domain.append(["tag_ids", "in", [tag_id]])
        if options.domain:
            domain.extend(self._parse_domain(options.domain))
        fields = [
            "id",
            "name",
            "description",
            "planned_hours",
            "date_deadline",
            "tag_ids",
            "stage_id",
            "user_id",
            "x_import_key",
        ]
        tasks = self.repo.find_tasks(domain, fields)
        for task in tasks:
            metadata = self._build_metadata(task)
            template_path = self._select_template(templates_empty_dir, metadata.task_type)
            template = load_template(template_path)
            content = render_markdown(template, task["name"], metadata, self._body_from_description(task))
            import_key = task.get("x_import_key") or str(task["id"])
            filename = f"{metadata.task_type}_{slugify(task['name'])}__{import_key}.md"
            out_path = export_out_dir / filename
            out_path.write_text(content, encoding="utf-8")
            report.add_item(str(out_path), "ok", f"Exported task '{task['name']}'.")
        return report

    def _find_tag_id(self, tag_name: str) -> int | None:
        results = self.repo.client.search_read("project.tags", [["name", "=", tag_name]], ["id"])
        return int(results[0]["id"]) if results else None

    def _build_metadata(self, task: dict) -> TaskMetadata:
        tag_names = self.repo.read_project_tags(task.get("tag_ids", []))
        task_type = self._extract_tag_value(tag_names, "type_") or "dev"
        priority = self._extract_tag_value(tag_names, "priority_") or "P2"
        moscow_raw = self._extract_tag_value(tag_names, "moscow_") or "must"
        moscow = self._normalize_moscow(moscow_raw)
        status = STAGE_TO_STATUS.get(task.get("stage_id", [None, ""])[1], "todo")
        estimation = hours_to_estimation(task.get("planned_hours"))
        owner = self._format_owner(task.get("user_id"))
        deadline = self._parse_deadline(task.get("date_deadline"))
        links = self._extract_links(task.get("description") or "")
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
        mapping = {"must": "Must", "should": "Should", "could": "Could", "wont": "Won’t"}
        return mapping.get(value.lower(), "Must")

    @staticmethod
    def _format_owner(user_field) -> str | None:
        if not user_field:
            return None
        if isinstance(user_field, list):
            return f"@{user_field[1]}"
        return f"@{user_field}"

    @staticmethod
    def _parse_deadline(value) -> date | None:
        if not value:
            return None
        if isinstance(value, str):
            return date.fromisoformat(value)
        return None

    @staticmethod
    def _extract_links(description: str) -> list[str]:
        match = re.search(r"^Liens:\s*(?:\n|- )(.*?)(?:\n\n|$)", description, re.S | re.M)
        if not match:
            return []
        block = match.group(1)
        return [line.strip("- ") for line in block.splitlines() if line.strip()]

    @staticmethod
    def _body_from_description(task: dict) -> str:
        description = task.get("description") or ""
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
