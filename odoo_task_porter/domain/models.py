"""Domain models."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TaskMetadata:
    """Normalized task metadata parsed from Markdown."""

    task_type: str
    status: str
    priority: str
    moscow: str
    estimation: str
    owner: str | None
    deadline: date | None
    links: list[str]


@dataclass(frozen=True)
class ParsedMarkdown:
    """Parsed markdown file content."""

    title: str
    metadata: TaskMetadata
    description: str
    raw_body: str
    source_path: Path
    task_code: str | None = None
    dependencies_blocking: list[str] = field(default_factory=list)
    dependencies_other: list[str] = field(default_factory=list)


@dataclass
class ReportItem:
    """Single report entry."""

    source: str
    status: str
    message: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class Report:
    """Execution report with errors and warnings."""

    items: list[ReportItem] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_item(self, source: str, status: str, message: str, **data: Any) -> None:
        self.items.append(ReportItem(source=source, status=status, message=message, data=data))

    def add_warning(self, warning: str) -> None:
        self.warnings.append(warning)

    def to_dict(self) -> dict[str, Any]:
        return {
            "items": [
                {
                    "source": item.source,
                    "status": item.status,
                    "message": item.message,
                    "data": item.data,
                }
                for item in self.items
            ],
            "warnings": self.warnings,
        }
