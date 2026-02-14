"""Service for scaffolding project workspaces from markdown templates."""
from __future__ import annotations

import re
import shutil
import unicodedata
from pathlib import Path

from odoo_task_porter.domain.models import Report

CADRAGE_TEMPLATE_FILES = [
    "prod_description_project_task.md",
    "prod_problematique_task.md",
    "prod_analyse_besoin_task.md",
    "gov_parties_prenantes_task.md",
    "prod_personas_user_stories_task.md",
    "prod_moscow_fonctionnalites_task.md",
    "prod_decoupage_mvp_versions_task.md",
    "risk_faisabilite_risques_task.md",
    "research_veille_techno_task.md",
    "prod_estimation_charge_task.md.md",
]


def slugify_project_name(value: str) -> str:
    """Turn a project name into a stable filesystem slug."""
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalized).strip("-").lower()
    return slug or "project"


class ProjectTemplateService:
    """Create a project folder with template and cadrage sections."""

    def run(
        self,
        project_name: str,
        output_dir: Path,
        templates_source_dir: Path,
        project_template_file: Path,
        force: bool = False,
    ) -> Report:
        if not project_name.strip():
            raise ValueError("Le nom du projet est obligatoire.")
        if not templates_source_dir.exists() or not templates_source_dir.is_dir():
            raise ValueError(f"Templates source introuvables: {templates_source_dir}")

        template_files = sorted(path for path in templates_source_dir.rglob("*.md") if path.is_file())
        if not template_files:
            raise ValueError(f"Aucun template .md trouve dans {templates_source_dir}")

        slug = slugify_project_name(project_name)
        project_dir = output_dir / slug
        if project_dir.exists() and not force:
            raise ValueError(
                f"Le dossier projet existe deja: {project_dir}. Utilise --force pour ecraser."
            )

        report = Report()
        if project_dir.exists() and force:
            shutil.rmtree(project_dir)
            report.add_warning(f"Dossier ecrase: {project_dir}")

        templates_dir = project_dir / "templates" / "tasks_templates"
        cadrage_dir = project_dir / "cadrage"
        specifications_dir = project_dir / "specifications"
        in_progress_dir = project_dir / "en_cours"
        for path in (templates_dir, cadrage_dir, specifications_dir, in_progress_dir):
            path.mkdir(parents=True, exist_ok=True)
            report.add_item(str(path), "ok", "Directory created")

        for source in template_files:
            relative = source.relative_to(templates_source_dir)
            destination = templates_dir / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            report.add_item(str(destination), "ok", "Template copied")

        cadrage_present = []
        for filename in CADRAGE_TEMPLATE_FILES:
            source = templates_source_dir / filename
            if not source.exists():
                report.add_warning(f"Template cadrage absent: {filename}")
                continue
            destination = cadrage_dir / filename
            shutil.copy2(source, destination)
            cadrage_present.append(filename)
            report.add_item(str(destination), "ok", "Cadrage template copied")

        template_content = self._load_project_template(project_template_file)
        templates_section = "\n".join(
            f"- [{path.relative_to(templates_dir).as_posix()}](templates/tasks_templates/{path.relative_to(templates_dir).as_posix()})"
            for path in sorted(templates_dir.rglob("*.md"))
        )
        cadrage_section = "\n".join(
            f"- [{name}](cadrage/{name})" for name in cadrage_present
        )
        rendered = (
            template_content.replace("{{project_name}}", project_name)
            .replace("{{templates_section}}", templates_section or "- Aucun template.")
            .replace("{{cadrage_section}}", cadrage_section or "- Aucun template cadrage.")
        )

        project_template_path = project_dir / "project_template.md"
        project_template_path.write_text(rendered, encoding="utf-8")
        report.add_item(str(project_template_path), "ok", "Project template generated")
        return report

    def _load_project_template(self, template_path: Path) -> str:
        if template_path.exists() and template_path.is_file():
            return template_path.read_text(encoding="utf-8")
        return (
            "# {{project_name}}\n\n"
            "## Templates\n"
            "{{templates_section}}\n\n"
            "## Cadrage\n"
            "{{cadrage_section}}\n\n"
            "## Specifications\n"
            "- A completer\n\n"
            "## En cours\n"
            "- A completer\n"
        )
