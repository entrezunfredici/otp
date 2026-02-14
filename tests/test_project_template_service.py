from pathlib import Path

import pytest

from odoo_task_porter.services.project_template_service import ProjectTemplateService


def test_project_template_service_generates_expected_structure(tmp_path: Path) -> None:
    source_dir = tmp_path / "templates_source"
    source_dir.mkdir(parents=True)
    (source_dir / "dev_feature_task.md").write_text("# Dev feature", encoding="utf-8")
    (source_dir / "prod_description_project_task.md").write_text(
        "# Cadrage description", encoding="utf-8"
    )
    (source_dir / "prod_problematique_task.md").write_text(
        "# Cadrage problematique", encoding="utf-8"
    )
    nested = source_dir / "core"
    nested.mkdir()
    (nested / "common_core_task.md").write_text("# Core", encoding="utf-8")

    project_template = tmp_path / "project_template.md"
    project_template.write_text(
        "# {{project_name}}\n\n## Templates\n{{templates_section}}\n\n## Cadrage\n{{cadrage_section}}\n",
        encoding="utf-8",
    )

    output_dir = tmp_path / "projects"
    report = ProjectTemplateService().run(
        project_name="Mon Projet Odoo",
        output_dir=output_dir,
        templates_source_dir=source_dir,
        project_template_file=project_template,
    )

    project_dir = output_dir / "mon-projet-odoo"
    assert project_dir.exists()
    assert (project_dir / "templates" / "tasks_templates" / "dev_feature_task.md").exists()
    assert (project_dir / "templates" / "tasks_templates" / "core" / "common_core_task.md").exists()
    assert (project_dir / "cadrage" / "prod_description_project_task.md").exists()
    assert (project_dir / "specifications").exists()
    assert (project_dir / "en_cours").exists()

    content = (project_dir / "project_template.md").read_text(encoding="utf-8")
    assert "# Mon Projet Odoo" in content
    assert "templates/tasks_templates/dev_feature_task.md" in content
    assert "cadrage/prod_description_project_task.md" in content
    assert report.items


def test_project_template_service_refuses_existing_project_without_force(tmp_path: Path) -> None:
    source_dir = tmp_path / "templates_source"
    source_dir.mkdir(parents=True)
    (source_dir / "dev_feature_task.md").write_text("# Dev feature", encoding="utf-8")

    output_dir = tmp_path / "projects"
    existing = output_dir / "demo"
    existing.mkdir(parents=True)

    with pytest.raises(ValueError):
        ProjectTemplateService().run(
            project_name="Demo",
            output_dir=output_dir,
            templates_source_dir=source_dir,
            project_template_file=tmp_path / "missing_template.md",
            force=False,
        )
