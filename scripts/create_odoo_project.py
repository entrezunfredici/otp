"""Utility script to scaffold a project from task templates."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from odoo_task_porter.services.project_template_service import ProjectTemplateService


def main() -> int:
    parser = argparse.ArgumentParser(description="Create an Odoo project scaffold.")
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("projects"))
    parser.add_argument(
        "--templates-source-dir",
        type=Path,
        default=Path("templates/tasks_templates"),
    )
    parser.add_argument(
        "--project-template-file",
        type=Path,
        default=Path("templates/project_template.md"),
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    report = ProjectTemplateService().run(
        project_name=args.project_name,
        output_dir=args.output_dir,
        templates_source_dir=args.templates_source_dir,
        project_template_file=args.project_template_file,
        force=args.force,
    )
    print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
