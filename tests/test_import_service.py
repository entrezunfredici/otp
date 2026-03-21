from pathlib import Path

from odoo_task_porter.domain.errors import OdooError
from odoo_task_porter.rules.ids import build_import_key, has_task_code
from odoo_task_porter.services.import_service import ImportService


class _Spec:
    version_name = "odoo_19"
    models = type("_Models", (), {"task": "project.task"})()


class _RepoStub:
    def __init__(
        self,
        existing_titles: set[str] | None = None,
        dependency_field: str | None = None,
        parent_field: str | None = None,
        import_key_field: str | None = None,
        existing_import_keys: dict[str, str] | None = None,
    ) -> None:
        self._dependency_field = dependency_field
        self._parent_field = parent_field
        self._import_key_field = import_key_field
        self.ensure_called = False
        self.stages_requested: list[tuple[int, str]] = []
        self.updated: list[str] = []
        self.created: list[str] = []
        self.task_id_by_title: dict[str, int] = {}
        self.title_by_task_id: dict[int, str] = {}
        self.import_key_by_task_id: dict[int, str] = {}
        self.task_id_by_import_key: dict[str, int] = {}
        self.next_id = 1
        self.dependencies_written: list[tuple[int, list[int], str]] = []
        self.parents_written: list[tuple[int, int, str]] = []
        self.upsert_values_by_title: dict[str, dict] = {}
        for title in sorted(existing_titles or set()):
            self._register_task(title)
        for import_key, title in (existing_import_keys or {}).items():
            task_id = self.task_id_by_title.get(title)
            if task_id is None:
                task_id = self._register_task(title)
            self.import_key_by_task_id[task_id] = import_key
            self.task_id_by_import_key[import_key] = task_id

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
            "import_key": self._import_key_field,
            "estimation_hours": None,
            "owner": None,
            "parent": self._parent_field,
        }

    def ensure_import_key_field(self, import_key_field: str | None = None) -> None:
        self.ensure_called = True
        if self._import_key_field is None:
            raise AssertionError(
                "ensure_import_key_field should not be called when import_key is missing"
            )

    def supports_dependency_field(self) -> str | None:
        return self._dependency_field

    def get_or_create_tag(self, name: str) -> int:
        return 1

    def get_or_create_stage(self, project_id: int, status: str) -> int:
        self.stages_requested.append((project_id, status))
        return 10

    def find_user(self, owner: str) -> int | None:
        return None

    def find_task_by_import_key(self, project_id: int, import_key: str):
        task_id = self.task_id_by_import_key.get(import_key)
        if task_id is None:
            return None
        return self._task_record(task_id)

    def find_task_by_project_and_name(self, project_id: int, task_name: str):
        task_id = self.task_id_by_title.get(task_name)
        if task_id is not None:
            return self._task_record(task_id)
        return None

    def find_task_by_id(self, project_id: int, task_id: int):
        if task_id in self.title_by_task_id:
            return self._task_record(task_id)
        return None

    def find_task_by_project_and_code(self, project_id: int, task_code: str):
        for title, task_id in self.task_id_by_title.items():
            if has_task_code(title, task_code):
                return self._task_record(task_id)
        return None

    def find_existing_task(
        self,
        project_id: int,
        import_key: str,
        task_name: str | None = None,
        task_code: str | None = None,
        source_task_id: int | None = None,
        source_import_key: str | None = None,
    ):
        existing = None
        if source_task_id is not None:
            existing = self.find_task_by_id(project_id, source_task_id)
        if existing is None and self._import_key_field and source_import_key:
            existing = self.find_task_by_import_key(project_id, source_import_key)
        if existing is None and self._import_key_field:
            existing = self.find_task_by_import_key(project_id, import_key)
        if existing is None and task_code:
            existing = self.find_task_by_project_and_code(project_id, task_code)
        if existing is None and task_name:
            existing = self.find_task_by_project_and_name(project_id, task_name)
        if existing is not None:
            return existing
        return None

    def upsert_task(
        self,
        project_id: int,
        values: dict,
        import_key: str,
        task_code: str | None = None,
        source_task_id: int | None = None,
        source_import_key: str | None = None,
    ) -> int:
        task_name = str(values["name"])
        self.upsert_values_by_title[task_name] = values
        existing = self.find_existing_task(
            project_id,
            import_key,
            task_name,
            task_code,
            source_task_id=source_task_id,
            source_import_key=source_import_key,
        )
        if existing is not None:
            task_id = int(existing["id"])
            old_title = self.title_by_task_id[task_id]
            if old_title != task_name:
                self.task_id_by_title.pop(old_title, None)
                self.task_id_by_title[task_name] = task_id
                self.title_by_task_id[task_id] = task_name
            if self._import_key_field:
                old_import_key = self.import_key_by_task_id.get(task_id)
                if old_import_key:
                    self.task_id_by_import_key.pop(old_import_key, None)
                self.import_key_by_task_id[task_id] = import_key
                self.task_id_by_import_key[import_key] = task_id
            self.updated.append(task_name)
            return task_id

        self.created.append(task_name)
        task_id = self._register_task(task_name)
        if self._import_key_field:
            self.import_key_by_task_id[task_id] = import_key
            self.task_id_by_import_key[import_key] = task_id
        return task_id

    def find_tasks(self, domain: list, fields: list[str]):
        if len(domain) < 2:
            return []
        task_code = str(domain[1][2])
        match = self.find_task_by_project_and_code(1, task_code)
        return [match] if match else []

    def add_dependencies(self, task_id: int, dependency_ids: list[int], field_name: str) -> None:
        self.dependencies_written.append((task_id, dependency_ids, field_name))

    def set_parent(self, task_id: int, parent_id: int, field_name: str) -> None:
        self.parents_written.append((task_id, parent_id, field_name))

    def fields(self, model: str, field_names: list[str]):
        return {}

    def update_task(self, task_id: int, values: dict) -> None:
        task_name = values.get("name")
        if isinstance(task_name, str):
            old_title = self.title_by_task_id[task_id]
            if old_title != task_name:
                self.task_id_by_title.pop(old_title, None)
                self.task_id_by_title[task_name] = task_id
                self.title_by_task_id[task_id] = task_name
            self.updated.append(task_name)

    def _register_task(self, title: str) -> int:
        task_id = self.next_id
        self.next_id += 1
        self.task_id_by_title[title] = task_id
        self.title_by_task_id[task_id] = title
        return task_id

    def _task_record(self, task_id: int) -> dict[str, int | str]:
        return {"id": task_id, "name": self.title_by_task_id[task_id]}


class _ScheduleRepairRepoStub(_RepoStub):
    def __init__(self, existing_titles: set[str] | None = None) -> None:
        super().__init__(existing_titles=existing_titles)
        self.repaired_updates: list[tuple[int, dict]] = []

    def fields(self, model: str, field_names: list[str]):
        return {
            "date_start": {"type": "datetime"},
            "date_end": {"type": "datetime"},
            "date_deadline": {"type": "date"},
        }

    def upsert_task(
        self,
        project_id: int,
        values: dict,
        import_key: str,
        task_code: str | None = None,
        source_task_id: int | None = None,
        source_import_key: str | None = None,
    ) -> int:
        existing = self.find_existing_task(
            project_id,
            import_key,
            str(values["name"]),
            task_code,
            source_task_id=source_task_id,
            source_import_key=source_import_key,
        )
        if existing is not None:
            raise OdooError(
                "Odoo RPC error during project.task.write: The operation cannot be completed: "
                "The planned start date must be before the planned end date."
            )
        return super().upsert_task(
            project_id,
            values,
            import_key,
            task_code=task_code,
            source_task_id=source_task_id,
            source_import_key=source_import_key,
        )

    def update_task(self, task_id: int, values: dict) -> None:
        self.repaired_updates.append((task_id, values))
        super().update_task(task_id, values)


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


def test_extract_dependency_code_supports_dotted_codes() -> None:
    line = "(Bloquante) M-01.1 - API Projects CRUD - Attendu: prerequis OK"
    assert ImportService._extract_dependency_code(line) == "M-01.1"


def test_has_task_code_does_not_match_parent_prefix_on_subtask() -> None:
    assert has_task_code("M-01.1 - API Projects CRUD", "M-01.1")
    assert not has_task_code("M-01.1 - API Projects CRUD", "M-01")


def test_extract_parent_task_code_for_subtask() -> None:
    assert ImportService._extract_parent_task_code("M-01.1") == "M-01"
    assert ImportService._extract_parent_task_code("M-01.1.2") == "M-01.1"
    assert ImportService._extract_parent_task_code("M-01") is None


def test_import_links_subtask_to_parent_task(tmp_path: Path) -> None:
    _write_task(
        tmp_path / "parent.md",
        "M-01 - Projet",
        task_id="M-01",
    )
    _write_task(
        tmp_path / "child.md",
        "M-01.1 - API Projects CRUD",
        task_id="M-01.1",
    )

    repo = _RepoStub(parent_field="parent_id")
    report = ImportService(repo).run(tmp_path, "Projet")

    assert all(item.status == "ok" for item in report.items)
    assert repo.parents_written == [
        (
            repo.task_id_by_title["M-01.1 - API Projects CRUD"],
            repo.task_id_by_title["M-01 - Projet"],
            "parent_id",
        )
    ]


def test_import_links_subtask_to_existing_parent_task(tmp_path: Path) -> None:
    _write_task(
        tmp_path / "child.md",
        "M-01.1 - API Projects CRUD",
        task_id="M-01.1",
    )

    repo = _RepoStub(
        existing_titles={"M-01 - Projet"},
        parent_field="parent_id",
    )
    report = ImportService(repo).run(tmp_path, "Projet")

    assert report.items[0].status == "ok"
    assert repo.parents_written == [
        (
            repo.task_id_by_title["M-01.1 - API Projects CRUD"],
            repo.task_id_by_title["M-01 - Projet"],
            "parent_id",
        )
    ]


def test_import_with_import_key_falls_back_to_task_code_when_title_changes(tmp_path: Path) -> None:
    old_title = "M-01.1 - API Projects CRUD"
    new_title = "M-01.1 — API Projects CRUD (list/create/update/archive)"
    task_file = tmp_path / "task.md"
    _write_task(task_file, new_title)

    repo = _RepoStub(
        existing_titles={old_title},
        import_key_field="x_import_key",
        existing_import_keys={build_import_key("Projet", old_title): old_title},
    )
    report = ImportService(repo).run(tmp_path, "Projet")

    assert report.items[0].status == "ok"
    assert "update task 'M-01.1 — API Projects CRUD (list/create/update/archive)'" in report.items[0].message
    assert repo.created == []
    assert repo.updated == [new_title]
    assert build_import_key("Projet", new_title, "M-01.1") in repo.task_id_by_import_key


def test_import_updates_exported_task_by_source_id_when_title_changes_without_code(tmp_path: Path) -> None:
    task_file = tmp_path / "task_renamed__1.md"
    _write_task(task_file, "Task Renamed")

    repo = _RepoStub(existing_titles={"Task Legacy"})
    report = ImportService(repo).run(tmp_path, "Projet")

    assert report.items[0].status == "ok"
    assert "update task 'Task Renamed'" in report.items[0].message
    assert repo.created == []
    assert repo.updated == ["Task Renamed"]


def test_import_skips_readme_markdown_files(tmp_path: Path) -> None:
    _write_task(tmp_path / "task.md", "Task A")
    (tmp_path / "README-lot-restant.md").write_text("# Notes\n", encoding="utf-8")

    repo = _RepoStub()
    report = ImportService(repo).run(tmp_path, "Projet")

    assert len(report.items) == 1
    assert report.items[0].source == "task.md"
    assert any("README-lot-restant.md" in warning for warning in report.warnings)


def test_import_repairs_invalid_schedule_and_retries_update(tmp_path: Path) -> None:
    _write_task(tmp_path / "task.md", "Task A")

    repo = _ScheduleRepairRepoStub(existing_titles={"Task A"})
    report = ImportService(repo).run(tmp_path, "Projet")

    assert report.items[0].status == "ok"
    assert report.items[0].data["task_id"] == repo.task_id_by_title["Task A"]
    assert repo.created == []
    assert repo.updated == ["Task A"]
    assert len(repo.repaired_updates) == 1
    _, repaired_values = repo.repaired_updates[0]
    assert "date_start" in repaired_values
    assert "date_end" in repaired_values
    assert any("planning Odoo incoherent detecte" in warning for warning in report.warnings)


def test_import_preserves_html_description_without_escaping(tmp_path: Path) -> None:
    task_file = tmp_path / "task_html.md"
    task_file.write_text(
        "\n".join(
            [
                "# Task HTML",
                "",
                "## Metadonnees",
                "- Type: doc",
                "- Statut: todo",
                "- Priorite: P1",
                "- MoSCoW: Must",
                "- Estimation: 2h",
                "- Liens: ",
                "",
                "## Description",
                "",
                "<p>Bloc <strong>HTML</strong></p>",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    repo = _RepoStub()
    report = ImportService(repo).run(tmp_path, "Projet")

    assert report.items[0].status == "ok"
    description = str(repo.upsert_values_by_title["Task HTML"]["description"])
    assert "<p>Bloc <strong>HTML</strong></p>" in description
    assert "&lt;p&gt;" not in description


def test_import_reports_progress(tmp_path: Path) -> None:
    _write_task(tmp_path / "task1.md", "Task 1")
    _write_task(tmp_path / "task2.md", "Task 2")

    repo = _RepoStub()
    calls: list[tuple[int, int]] = []
    report = ImportService(repo).run(
        tmp_path,
        "Projet",
        on_progress=lambda done, total: calls.append((done, total)),
    )

    assert len(report.items) == 2
    assert calls[0] == (0, 2)
    assert calls[-1] == (2, 2)


def test_import_preserves_custom_stage_name(tmp_path: Path) -> None:
    task_file = tmp_path / "task.md"
    task_file.write_text(
        "\n".join(
            [
                "# M-01.2 - API Spaces CRUD",
                "",
                "## Metadonnees",
                "- ID: M-01.2",
                "- Type: dev",
                "- Statut: spécification",
                "- Priorite: P1",
                "- MoSCoW: Must",
                "- Estimation: S",
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

    repo = _RepoStub()
    report = ImportService(repo).run(tmp_path, "Projet")

    assert report.items[0].status == "ok"
    assert repo.stages_requested == [(1, "spécification")]
