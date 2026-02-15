from pathlib import Path

from odoo_task_porter.services.import_service import ImportService


class _Spec:
    version_name = "odoo_19"


class _RepoStub:
    def __init__(self, existing_titles: set[str] | None = None) -> None:
        self._existing_titles = set(existing_titles or set())
        self.ensure_called = False
        self.updated: list[str] = []
        self.created: list[str] = []

    def get_server_major_version(self) -> int | None:
        return 19

    def get_version_spec(self):
        return _Spec()

    def get_project_id(self, project_name: str) -> int:
        return 1

    def resolve_task_fields(self) -> dict[str, str | None]:
        return {
            "id": "id",
            "name": "name",
            "description": "description",
            "project": "project_id",
            "tags": "tag_ids",
            "stage": "stage_id",
            "deadline": None,
            "import_key": None,
            "estimation_hours": None,
            "owner": None,
        }

    def ensure_import_key_field(self, import_key_field: str | None = None) -> None:
        self.ensure_called = True
        raise AssertionError("ensure_import_key_field should not be called when import_key is missing")

    def supports_dependency_field(self) -> str | None:
        return None

    def get_or_create_tag(self, name: str) -> int:
        return 1

    def get_or_create_stage(self, project_id: int, status: str) -> int:
        return 10

    def find_user(self, owner: str) -> int | None:
        return None

    def find_task_by_import_key(self, project_id: int, import_key: str):
        return None

    def find_task_by_project_and_name(self, project_id: int, task_name: str):
        if task_name in self._existing_titles:
            return {"id": 42, "name": task_name}
        return None

    def upsert_task(self, project_id: int, values: dict, import_key: str) -> int:
        task_name = str(values["name"])
        if task_name in self._existing_titles:
            self.updated.append(task_name)
            return 42
        self._existing_titles.add(task_name)
        self.created.append(task_name)
        return 99


def _write_task(path: Path, title: str) -> None:
    path.write_text(
        "\n".join(
            [
                f"# {title}",
                "",
                "## Métadonnées",
                "- Type: doc",
                "- Statut: todo",
                "- Priorité: P1",
                "- MoSCoW: Must",
                "- Estimation: 2h",
                "- Owner: ",
                "- Deadline: ",
                "- Liens: ",
                "",
                "## Description",
                "Contenu.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_import_without_import_key_updates_by_title(tmp_path: Path) -> None:
    task_file = tmp_path / "task.md"
    _write_task(task_file, "Task A")

    repo = _RepoStub(existing_titles={"Task A"})
    report = ImportService(repo).run(tmp_path, "Projet")

    assert any("fallback sur le titre" in warning for warning in report.warnings)
    assert report.items[0].status == "ok"
    assert "update task 'Task A'" in report.items[0].message
    assert repo.updated == ["Task A"]
    assert repo.ensure_called is False


def test_import_without_import_key_creates_when_missing(tmp_path: Path) -> None:
    task_file = tmp_path / "task.md"
    _write_task(task_file, "Task B")

    repo = _RepoStub(existing_titles=set())
    report = ImportService(repo).run(tmp_path, "Projet")

    assert report.items[0].status == "ok"
    assert "create task 'Task B'" in report.items[0].message
    assert repo.created == ["Task B"]
    assert repo.ensure_called is False
