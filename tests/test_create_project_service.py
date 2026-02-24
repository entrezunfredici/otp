import pytest

from odoo_task_porter.services.create_project_service import CreateProjectService


class _RepoStub:
    def __init__(self, existing_id=None):
        self.existing_id = existing_id
        self.created_names: list[str] = []
        self.stages_requested: list[tuple[int, str]] = []

    def find_project_id(self, project_name: str):
        return self.existing_id

    def create_project(self, project_name: str) -> int:
        self.created_names.append(project_name)
        return 42

    def get_or_create_stage(self, project_id: int, status: str) -> int:
        self.stages_requested.append((project_id, status))
        return 100


def test_create_project_creates_project_when_missing() -> None:
    repo = _RepoStub(existing_id=None)
    report = CreateProjectService(repo).run(
        "Nouveau Projet",
        with_default_sections=False,
        with_default_tasks=False,
    )
    assert repo.created_names == ["Nouveau Projet"]
    assert len(report.items) == 1
    assert report.items[0].status == "ok"
    assert report.items[0].data["project_id"] == 42


def test_create_project_fails_when_already_exists() -> None:
    repo = _RepoStub(existing_id=7)
    with pytest.raises(ValueError):
        CreateProjectService(repo).run(
            "Existant",
            with_default_sections=False,
            with_default_tasks=False,
        )


def test_create_project_allows_existing_when_flag_is_set() -> None:
    repo = _RepoStub(existing_id=7)
    report = CreateProjectService(repo).run(
        "Existant",
        with_default_sections=False,
        with_default_tasks=False,
        allow_existing=True,
    )
    assert repo.created_names == []
    assert report.warnings


def test_parse_project_plan_from_markdown_sections() -> None:
    template = """
## Etapes des taches
### Ressources
- prod_description_project_task.md | 1.0-2.0
### Backlog
- prod_analyse_besoin_task.md

## Specifications
- ...
"""
    plan = CreateProjectService._parse_project_plan(template)
    assert plan.stage_names == ["Ressources", "Backlog"]
    assert plan.task_stage_by_template["prod_description_project_task.md"] == "Ressources"
    assert plan.task_stage_by_template["prod_analyse_besoin_task.md"] == "Backlog"
    assert plan.task_durations_hours["prod_description_project_task.md"] == (1.0, 2.0)
