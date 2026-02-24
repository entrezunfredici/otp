"""Markdown parsing and rendering."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from html import escape
from pathlib import Path
import re
from typing import Iterable

from odoo_task_porter.domain.errors import ValidationError
from odoo_task_porter.domain.models import ParsedMarkdown, TaskMetadata
from odoo_task_porter.rules.validate import require_fields, validate_metadata

META_SECTION_HEADERS = {
    "## Metadonnees",
    "## M\u00e9tadonn\u00e9es",
    "## M\u00c3\u00a9tadonn\u00c3\u00a9es",
    "## M\u00c3\u0192\u00c2\u00a9tadonn\u00c3\u0192\u00c2\u00a9es",
    "## M\u00c3\u0192\u00c6\u2019\u00c3\u201a\u00c2\u00a9tadonn\u00c3\u0192\u00c6\u2019\u00c3\u201a\u00c2\u00a9es",
}
DEPENDENCIES_HEADERS = {
    "## Dependances & risques",
    "## D\u00e9pendances & risques",
    "## D\u00c3\u00a9pendances & risques",
    "## D\u00c3\u0192\u00c2\u00a9pendances & risques",
    "## D\u00c3\u0192\u00c6\u2019\u00c3\u201a\u00c2\u00a9pendances & risques",
}
DEPENDENCIES_LABELS = (
    "Dependances",
    "D\u00e9pendances",
    "D\u00c3\u00a9pendances",
    "D\u00c3\u0192\u00c2\u00a9pendances",
    "D\u00c3\u0192\u00c6\u2019\u00c3\u201a\u00c2\u00a9pendances",
)

META_FIELD_MAP = {
    "id": "id",
    "type": "type",
    "statut": "statut",
    "priorite": "priority",
    "priorit\u00e9": "priority",
    "priorit\u00c3\u00a9": "priority",
    "priorit\u00c3\u0192\u00c2\u00a9": "priority",
    "priorit\u00c3\u0192\u00c2\u00a3\u00c3\u201a\u00c2\u00a9": "priority",
    "priorit\u00c3\u0192\u00c6\u2019\u00c3\u201a\u00c2\u00a9": "priority",
    "moscow": "moscow",
    "estimation": "estimation",
    "owner": "owner",
    "deadline": "deadline",
    "liens": "liens",
}

TABLE_SEPARATOR_RE = re.compile(r"^\|?[\s:~\-\u2013\u2014]+(?:\|[\s:~\-\u2013\u2014]+)+\|?$")
CHECKBOX_MARK_RE = re.compile(r"^\[( |x|X|✓|✔|☑)\]\s+(.*)$")
UNICODE_CHECKBOX_RE = re.compile(r"^(☐|☑|✅)\s+(.*)$")
HTML_TAG_RE = re.compile(
    r"<\s*/?\s*(?:p|ul|ol|li|h[1-6]|table|thead|tbody|tr|td|th|div|span|strong|em|a|blockquote|br)\b",
    re.I,
)


@dataclass(frozen=True)
class MarkdownTemplate:
    """Represents a markdown template file."""

    name: str
    content: str


def parse_markdown(path: Path) -> ParsedMarkdown:
    """Parse markdown file into structured data."""
    text = path.read_text(encoding="utf-8")
    lines = _drop_leading_blank_lines(_strip_front_matter(text.splitlines()))
    first_line = lines[0].lstrip("\ufeff") if lines else ""
    if not lines or not first_line.startswith("# "):
        raise ValidationError("Le fichier doit commencer par un titre '#'.")
    title = first_line.lstrip("# ").strip()
    metadata_values = _extract_metadata(lines)
    require_fields(metadata_values, ["type", "statut", "priority", "moscow", "estimation"])
    task_metadata = TaskMetadata(
        task_type=metadata_values.get("type", ""),
        status=metadata_values.get("statut", ""),
        priority=metadata_values.get("priority", ""),
        moscow=metadata_values.get("moscow", ""),
        estimation=metadata_values.get("estimation", ""),
        owner=metadata_values.get("owner"),
        deadline=_parse_date(metadata_values.get("deadline")),
        links=_parse_links(metadata_values.get("liens", "")),
    )
    validate_metadata(task_metadata)
    task_code = _extract_task_code(metadata_values.get("id"), title)
    body, dependencies_blocking, dependencies_other = _extract_body(lines)
    return ParsedMarkdown(
        title=title,
        metadata=task_metadata,
        description=body.strip(),
        raw_body=text,
        source_path=path,
        task_code=task_code,
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


def markdown_to_odoo_html(markdown_text: str) -> str:
    """Convert a markdown subset to HTML suited for Odoo descriptions."""
    lines = markdown_text.splitlines()
    html_parts: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue

        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            level = max(1, min(6, level))
            content = stripped[level:].strip()
            html_parts.append(f"<h{level}>{_render_inline_markdown(content)}</h{level}>")
            i += 1
            continue

        if _is_table_header(lines, i):
            table_html, next_index = _render_table(lines, i)
            html_parts.append(table_html)
            i = next_index
            continue

        if _is_unordered_item(stripped):
            list_html, next_index = _render_unordered_list(lines, i)
            html_parts.append(list_html)
            i = next_index
            continue

        if _is_ordered_item(stripped):
            list_html, next_index = _render_ordered_list(lines, i)
            html_parts.append(list_html)
            i = next_index
            continue

        paragraph_lines = [stripped]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if not nxt:
                break
            if nxt.startswith("#") or _is_unordered_item(nxt) or _is_ordered_item(nxt):
                break
            if _is_table_header(lines, i):
                break
            paragraph_lines.append(nxt)
            i += 1
        html_parts.append(f"<p>{_render_inline_markdown(' '.join(paragraph_lines))}</p>")

    if not html_parts:
        return "<p></p>"
    return "\n".join(html_parts)


def is_odoo_html_fragment(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    if not stripped.startswith("<"):
        return False
    return HTML_TAG_RE.search(stripped) is not None


def html_to_odoo_html(html_text: str) -> str:
    stripped = html_text.strip()
    if not stripped:
        return "<p></p>"
    return stripped


def _extract_metadata(lines: list[str]) -> dict[str, str]:
    start_index: int | None = None
    for index, line in enumerate(lines):
        if line in META_SECTION_HEADERS:
            start_index = index + 1
            break
    if start_index is None:
        raise ValidationError("Section '## Metadonnees' manquante.")

    values: dict[str, str] = {}
    for line in lines[start_index:]:
        if line.startswith("## "):
            break
        if line.startswith("- "):
            match = re.match(r"^-\s*([^:]+):\s*(.*)$", line)
            if not match:
                continue
            key_raw, value = match.groups()
            key = _normalize_metadata_key(key_raw)
            mapped = META_FIELD_MAP.get(key)
            if mapped:
                values[mapped] = _sanitize_metadata_value(mapped, _normalize_metadata_value(value))
    return values


def _extract_body(lines: list[str]) -> tuple[str, list[str], list[str]]:
    """Return body without metadata section and parse dependencies."""
    body_lines: list[str] = []
    skip = False
    dependencies_blocking: list[str] = []
    dependencies_other: list[str] = []
    for line in lines[1:]:
        if line in META_SECTION_HEADERS:
            skip = True
            continue
        if skip and line.startswith("## ") and line not in META_SECTION_HEADERS:
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
    if value.strip().upper() == "YYYY-MM-DD":
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValidationError(f"Deadline invalide: {value}") from error


def _parse_links(value: str) -> list[str]:
    if not value:
        return []
    stripped = value.strip()
    if stripped.startswith("(") and stripped.endswith(")"):
        return []
    parts = [item.strip() for item in value.split(",") if item.strip()]
    return parts


def _parse_dependencies(lines: Iterable[str]) -> tuple[list[str], list[str]]:
    line_list = list(lines)
    dep_index: int | None = None
    for index, line in enumerate(line_list):
        if line in DEPENDENCIES_HEADERS:
            dep_index = index + 1
            break
    if dep_index is None:
        return [], []

    blocking: list[str] = []
    other: list[str] = []
    in_dependencies = False
    for line in line_list[dep_index:]:
        if line.startswith("## "):
            break
        if any(line.strip().startswith(label) for label in DEPENDENCIES_LABELS):
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


def _extract_task_code(metadata_id: str | None, title: str) -> str | None:
    for source in (metadata_id or "", title):
        match = re.search(r"\b([A-Za-z]+-\d+)\b", source)
        if match:
            return match.group(1).upper()
    return None


def _sanitize_metadata_value(field: str, value: str) -> str:
    if not value:
        return value
    if "|" in value:
        value = value.split("|", 1)[0].strip()
    if field == "estimation" and "/" in value:
        value = value.split("/", 1)[0].strip()
    if field == "owner" and value == "@":
        return ""
    if field == "deadline" and value.upper() == "YYYY-MM-DD":
        return ""
    if field == "liens" and value.startswith("(") and value.endswith(")"):
        return ""
    if field == "moscow":
        value = value.replace("Won''t", "Won't").replace("Won\u00c3\u0192\u00c2\u00a2\u00c3\u00a2\u20ac\u0161\u00c2\u00ac\u00c3\u00a2\u20ac\u017e\u00c2\u00a2t", "Won't")
    return value


def _strip_front_matter(lines: list[str]) -> list[str]:
    if not lines:
        return lines
    if lines[0].lstrip("\ufeff").strip() != "---":
        return lines
    end_index: int | None = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end_index = index
            break
    if end_index is None:
        return lines
    return lines[end_index + 1 :]


def _drop_leading_blank_lines(lines: list[str]) -> list[str]:
    index = 0
    while index < len(lines) and not lines[index].strip():
        index += 1
    return lines[index:]


def _normalize_metadata_key(raw: str) -> str:
    key = re.sub(r"[*`_]", "", raw).strip().lower()
    return key


def _normalize_metadata_value(value: str) -> str:
    normalized = value.strip()
    if len(normalized) >= 2 and normalized.startswith("`") and normalized.endswith("`"):
        return normalized[1:-1].strip()
    return normalized


def _is_unordered_item(stripped_line: str) -> bool:
    return stripped_line.startswith("- ") or stripped_line.startswith("* ") or stripped_line.startswith("+ ")


def _is_ordered_item(stripped_line: str) -> bool:
    return re.match(r"^\d+\.\s+", stripped_line) is not None


def _is_table_header(lines: list[str], index: int) -> bool:
    if index + 1 >= len(lines):
        return False
    header = lines[index].strip()
    separator = lines[index + 1].strip()
    if "|" not in header:
        return False
    return TABLE_SEPARATOR_RE.match(separator) is not None


def _render_table(lines: list[str], start_index: int) -> tuple[str, int]:
    header_cells = _split_table_row(lines[start_index].strip())
    i = start_index + 2
    body_rows: list[list[str]] = []
    while i < len(lines):
        row = lines[i].strip()
        if not row or "|" not in row:
            break
        body_rows.append(_split_table_row(row))
        i += 1

    head_html = "".join(f"<th>{_render_inline_markdown(cell)}</th>" for cell in header_cells)
    body_html_parts: list[str] = []
    for row in body_rows:
        cells_html = "".join(f"<td>{_render_inline_markdown(cell)}</td>" for cell in row)
        body_html_parts.append(f"<tr>{cells_html}</tr>")
    body_html = "".join(body_html_parts)
    return (
        "<table class=\"table table-sm table-bordered\">"
        f"<thead><tr>{head_html}</tr></thead><tbody>{body_html}</tbody></table>",
        i,
    )


def _split_table_row(row: str) -> list[str]:
    trimmed = row.strip("|")
    return [cell.strip() for cell in trimmed.split("|")]


def _render_unordered_list(lines: list[str], start_index: int) -> tuple[str, int]:
    i = start_index
    items: list[tuple[bool, bool, str]] = []
    while i < len(lines):
        stripped = lines[i].strip()
        if not _is_unordered_item(stripped):
            break
        content = stripped[2:].strip()
        checkbox_match = CHECKBOX_MARK_RE.match(content)
        if checkbox_match:
            checked = checkbox_match.group(1) in {"x", "X", "✓", "✔", "☑"}
            label = _render_inline_markdown(checkbox_match.group(2).strip())
            items.append((True, checked, label))
            i += 1
            continue

        unicode_checkbox_match = UNICODE_CHECKBOX_RE.match(content)
        if unicode_checkbox_match:
            checked = unicode_checkbox_match.group(1) in {"☑", "✅"}
            label = _render_inline_markdown(unicode_checkbox_match.group(2).strip())
            items.append((True, checked, label))
            i += 1
            continue

        items.append((False, False, _render_inline_markdown(content)))
        i += 1

    if any(is_checkbox for is_checkbox, _, _ in items):
        rendered_items = []
        for is_checkbox, checked, label in items:
            classes = []
            if is_checkbox and checked:
                classes.append("o_checked")
            class_attr = f' class="{" ".join(classes)}"' if classes else ""
            rendered_items.append(f"<li{class_attr}>{label}</li>")
        return f'<ul class="o_checklist">{"".join(rendered_items)}</ul>', i

    rendered_items = [f"<li>{label}</li>" for _, _, label in items]
    return f"<ul>{''.join(rendered_items)}</ul>", i


def _render_ordered_list(lines: list[str], start_index: int) -> tuple[str, int]:
    i = start_index
    items: list[str] = []
    while i < len(lines):
        stripped = lines[i].strip()
        match = re.match(r"^\d+\.\s+(.*)$", stripped)
        if not match:
            break
        items.append(f"<li>{_render_inline_markdown(match.group(1).strip())}</li>")
        i += 1
    return f"<ol>{''.join(items)}</ol>", i


def _render_inline_markdown(text: str) -> str:
    rendered = escape(text, quote=True)
    rendered = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>',
        rendered,
    )
    rendered = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", rendered)
    rendered = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", rendered)
    rendered = re.sub(r"`([^`]+)`", r"<code>\1</code>", rendered)
    return rendered
