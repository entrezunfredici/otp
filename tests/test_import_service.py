from pathlib import Path

from odoo_task_porter.services.import_service import ImportService


class _Spec:
    version_name = "odoo_19"


class _RepoStub:
    def __init__(
        self,
        existing_titles: set[str] | None = None,
        dependency_field: str | None = None,
    ) -> None:
        self._existing_titles = set(existing_titles or set())
        self._dependency_field = dependency_field
        self.ensure_called = False
        self.updated: list[str] = []
        self.created: list[str] = []
        self.task_id_by_title: dict[str, int] = {
            title: index + 1 for index, title in enumerate(sorted(self._existing_titles))
        }
        self.next_id = len(self.task_id_by_title) + 1
        self.dependencies_written: list[tuple[int, list[int], str]] = []

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
        return self._dependency_field

    def get_or_create_tag(self, name: str) -> int:
        return 1

    def get_or_create_stage(self, project_id: int, status: str) -> int:
        return 10

    def find_user(self, owner: str) -> int | None:
        return None

    def find_task_by_import_key(self, project_id: int, import_key: str):
        return None

    def find_task_by_project_and_name(self, project_id: int, task_name: str):
        task_id = self.task_id_by_title.get(task_name)
        if task_id is not None:
            return {"id": task_id, "name": task_name}
        return None

    def upsert_task(self, project_id: int, values: dict, import_key: str) -> int:
        task_name = str(values["name"])
        if task_name in self.task_id_by_title:
            self.updated.append(task_name)
            return self.task_id_by_title[task_name]

        self.created.append(task_name)
        task_id = self.next_id
        self.next_id += 1
        self.task_id_by_title[task_name] = task_id
        return task_id

    def find_tasks(self, domain: list, fields: list[str]):
        if len(domain) < 2:
            return []
        task_code = str(domain[1][2]).upper()
        for title, task_id in self.task_id_by_title.items():
            if task_code in title.upper():
                return [{"id": task_id, "name": title}]
        return []

    def add_dependencies(self, task_id: int, dependency_ids: list[int], field_name: str) -> None:
        self.dependencies_written.append((task_id, dependency_ids, field_name))


def _write_task(path: Path, title: str, dependencies: str | None = None, task_id: str | None = None) -> None:
    lines = [
        f"# {title}",
        "",
        "## Metadonnees",
        f"- ID: {task_id or ''}",
        "- Type: doc",
        "- Statut: todo",
        "- Priorite: P1",
        "- MoSCoW: Must",
        "- Estimation: 2h",
        "- Owner: ",
        "- Deadline: ",
        "- Liens: ",
        "",
        "## Description",
        "Contenu.",
    ]
    if dependencies is not None:
        lines.extend(
            [
                "",
                "## Dependances & risques",
                "Dependances:",
                dependencies,
            ]
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


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


def test_import_applies_blocking_dependency_by_task_code(tmp_path: Path) -> None:
    _write_task(
        tmp_path / "dep.md",
        "D-101 - Initialiser repo",
        task_id="D-101",
    )
    _write_task(
        tmp_path / "main.md",
        "D-102 - Docker Compose",
        dependencies="- (Bloquante) D-101 - (voir tache) - Owner: @alice - Attendu: prerequis OK",
        task_id="D-102",
    )

    repo = _RepoStub(dependency_field="depend_on_ids")
    report = ImportService(repo).run(tmp_path, "Projet")

    assert all(item.status == "ok" for item in report.items)
    assert len(repo.dependencies_written) == 1
    dependent_task_id, dependency_ids, field_name = repo.dependencies_written[0]
    assert field_name == "depend_on_ids"
    assert dependent_task_id == repo.task_id_by_title["D-102 - Docker Compose"]
    assert dependency_ids == [repo.task_id_by_title["D-101 - Initialiser repo"]]


def test_extract_dependency_code_from_expected_format() -> None:
    line = "(Bloquante) D-101 - (voir tache) - Owner: @Frederic Macabiau - Attendu: prerequis OK"
    assert ImportService._extract_dependency_code(line) == "D-101"
