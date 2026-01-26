"""Service for linting markdown tasks."""
from __future__ import annotations

from pathlib import Path

from odoo_task_porter.adapters.markdown import parse_markdown
from odoo_task_porter.domain.errors import ValidationError
from odoo_task_porter.domain.models import Report


class LintService:
    """Validate markdown tasks without talking to Odoo."""

    def run(self, tasks_md_dir: Path) -> Report:
        report = Report()
        for path in sorted(tasks_md_dir.glob("*.md")):
            try:
                parse_markdown(path)
                report.add_item(path.name, "ok", "Valid task file.")
            except ValidationError as error:
                report.add_item(path.name, "error", str(error))
            except Exception as error:  # noqa: BLE001
                report.add_item(path.name, "error", str(error))
        return report
