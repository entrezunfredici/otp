"""Markdown parsing and rendering."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re
from typing import Iterable

from odoo_task_porter.domain.errors import ValidationError
from odoo_task_porter.domain.models import ParsedMarkdown, TaskMetadata
from odoo_task_porter.rules.validate import require_fields, validate_metadata

META_SECTION_HEADER = "## Métadonnées"
DEPENDENCIES_HEADER = "## Dépendances & risques"

META_FIELD_MAP = {
    "id": "id",
    "type": "type",
    "statut": "statut",
    "priorité": "priorité",
    "moscow": "moscow",
    "estimation": "estimation",
    "owner": "owner",
    "deadline": "deadline",
    "liens": "liens",
}


@dataclass(frozen=True)
class MarkdownTemplate:
    """Represents a markdown template file."""

    name: str
    content: str


def parse_markdown(path: Path) -> ParsedMarkdown:
    """Parse markdown file into structured data."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or not lines[0].startswith("# "):
        raise ValidationError("Le fichier doit commencer par un titre '#'.")
    title = lines[0].lstrip("# ").strip()
    metadata_values = _extract_metadata(lines)
    require_fields(metadata_values, ["type", "statut", "priorité", "moscow", "estimation"])
    task_metadata = TaskMetadata(
        task_type=metadata_values.get("type", ""),
        status=metadata_values.get("statut", ""),
        priority=metadata_values.get("priorité", ""),
        moscow=metadata_values.get("moscow", ""),
        estimation=metadata_values.get("estimation", ""),
        owner=metadata_values.get("owner"),
        deadline=_parse_date(metadata_values.get("deadline")),
        links=_parse_links(metadata_values.get("liens", "")),
    )
    validate_metadata(task_metadata)
    body, dependencies_blocking, dependencies_other = _extract_body(lines)
    return ParsedMarkdown(
        title=title,
        metadata=task_metadata,
        description=body.strip(),
        raw_body=text,
        source_path=path,
        dependencies_blocking=dependencies_blocking,
        dependencies_other=dependencies_other,
    )


def render_markdown(template: MarkdownTemplate, title: str, metadata: TaskMetadata, body: str) -> str:
    """Render a markdown file from a template and data."""
    rendered = template.content
    replacements = {
        "{{TITLE}}": title,
        "{{TYPE}}": metadata.task_type,
        "{{STATUT}}": metadata.status,
        "{{PRIORITE}}": metadata.priority,
        "{{MOSCOW}}": metadata.moscow,
        "{{ESTIMATION}}": metadata.estimation,
        "{{OWNER}}": metadata.owner or "",
        "{{DEADLINE}}": metadata.deadline.isoformat() if metadata.deadline else "",
        "{{LIENS}}": "\n".join(metadata.links),
        "{{DESCRIPTION}}": body.strip(),
    }
    for key, value in replacements.items():
        rendered = rendered.replace(key, value)
    return rendered.strip() + "\n"


def load_template(path: Path) -> MarkdownTemplate:
    return MarkdownTemplate(name=path.name, content=path.read_text(encoding="utf-8"))


def _extract_metadata(lines: list[str]) -> dict[str, str]:
    if META_SECTION_HEADER not in lines:
        raise ValidationError("Section '## Métadonnées' manquante.")
    start_index = lines.index(META_SECTION_HEADER) + 1
    values: dict[str, str] = {}
    for line in lines[start_index:]:
        if line.startswith("## "):
            break
        if line.strip().startswith("-"):
            match = re.match(r"^-\s*([^:]+):\s*(.*)$", line.strip())
            if not match:
                continue
            key_raw, value = match.groups()
            key = key_raw.strip().lower()
            mapped = META_FIELD_MAP.get(key)
            if mapped:
                if mapped == "id":
                    continue
                values[mapped] = value.strip()
    return values


def _extract_body(lines: list[str]) -> tuple[str, list[str], list[str]]:
    """Return body without metadata section and parse dependencies."""
    body_lines: list[str] = []
    skip = False
    dependencies_blocking: list[str] = []
    dependencies_other: list[str] = []
    for line in lines[1:]:
        if line.startswith(META_SECTION_HEADER):
            skip = True
            continue
        if skip and line.startswith("## ") and line != META_SECTION_HEADER:
            skip = False
        if skip:
            continue
        body_lines.append(line)
    body = "\n".join(body_lines)
    dependencies_blocking, dependencies_other = _parse_dependencies(lines)
    return body, dependencies_blocking, dependencies_other


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def _parse_links(value: str) -> list[str]:
    if not value:
        return []
    parts = [item.strip() for item in value.split(",") if item.strip()]
    return parts


def _parse_dependencies(lines: Iterable[str]) -> tuple[list[str], list[str]]:
    if DEPENDENCIES_HEADER not in lines:
        return [], []
    start = list(lines).index(DEPENDENCIES_HEADER) + 1
    blocking: list[str] = []
    other: list[str] = []
    in_dependencies = False
    for line in list(lines)[start:]:
        if line.startswith("## "):
            break
        if line.strip().startswith("Dépendances"):
            in_dependencies = True
            continue
        if not in_dependencies:
            continue
        if line.strip().startswith("-"):
            content = line.strip("- ")
            if content.startswith("(Bloquante)"):
                blocking.append(content)
            else:
                other.append(content)
    return blocking, other
