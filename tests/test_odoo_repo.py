from __future__ import annotations

import pytest

from odoo_task_porter.adapters.odoo_repo import OdooRepository
from odoo_task_porter.domain.errors import OdooError
from odoo_task_porter.rules.ids import build_import_key


class _BackendStub:
    def __init__(self, tasks: list[dict], write_result: bool = True) -> None:
        self.tasks = tasks
        self.write_result = write_result
        self.last_write: tuple[str, list[int], dict] | None = None

    def get_server_major_version(self) -> int | None:
        return 19

    def fields_get(self, model: str, fields: list[str] | None = None) -> dict[str, dict[str, str]]:
        assert model == "project.task"
        available = {
            "id": {"type": "integer"},
            "name": {"type": "char"},
            "description": {"type": "html"},
            "project_id": {"type": "many2one"},
            "tag_ids": {"type": "many2many"},
            "stage_id": {"type": "many2one"},
            "x_import_key": {"type": "char"},
        }
        if fields:
            return {name: meta for name, meta in available.items() if name in fields}
        return available

    def search_read(self, model: str, domain: list, fields: list[str]) -> list[dict]:
        assert model == "project.task"
        results = list(self.tasks)
        for entry in domain:
            field_name, operator, expected = entry
            if field_name == "id" and operator == "=":
                results = [task for task in results if task["id"] == expected]
            elif field_name == "project_id" and operator == "=":
                results = [task for task in results if task["project_id"] == expected]
            elif field_name == "x_import_key" and operator == "=":
                results = [task for task in results if task.get("x_import_key") == expected]
            elif field_name == "name" and operator == "=":
                results = [task for task in results if task["name"] == expected]
            elif field_name == "name" and operator == "ilike":
                needle = str(expected).lower()
                results = [task for task in results if needle in task["name"].lower()]
            else:
                raise AssertionError(f"unsupported domain: {entry}")
        return [{field: task[field] for field in fields} for task in results]

    def write(self, model: str, ids: list[int], values: dict) -> bool:
        assert model == "project.task"
        self.last_write = (model, ids, values)
        return self.write_result

    def create(self, model: str, values: dict) -> int:
        assert model == "project.task"
        return 999


class _StageBackendStub:
    def __init__(self) -> None:
        self.last_stage_create: tuple[str, dict] | None = None

    def get_server_major_version(self) -> int | None:
        return 19

    def fields_get(self, model: str, fields: list[str] | None = None) -> dict[str, dict[str, str]]:
        if model == "project.task":
            return {
                "id": {"type": "integer"},
                "name": {"type": "char"},
                "description": {"type": "html"},
                "project_id": {"type": "many2one"},
                "tag_ids": {"type": "many2many"},
                "stage_id": {"type": "many2one"},
            }
        if model == "project.task.type":
            available = {
                "id": {"type": "integer"},
                "name": {"type": "char"},
                "project_ids": {"type": "many2many"},
            }
            if fields:
                return {name: meta for name, meta in available.items() if name in fields}
            return available
        raise AssertionError(f"unexpected model: {model}")

    def search_read(self, model: str, domain: list, fields: list[str]) -> list[dict]:
        if model == "project.task.type":
            return []
        raise AssertionError(f"unexpected model: {model}")

    def create(self, model: str, values: dict) -> int:
        assert model == "project.task.type"
        self.last_stage_create = (model, values)
        return 321

    def write(self, model: str, ids: list[int], values: dict) -> bool:
        raise AssertionError("write should not be called in this test")


def test_find_existing_task_falls_back_to_normalized_name_when_code_missing() -> None:
    backend = _BackendStub(
        tasks=[
            {
                "id": 12,
                "name": "API Spaces CRUD",
                "project_id": 1,
                "x_import_key": build_import_key("Projet", "API Spaces CRUD"),
            }
        ]
    )
    repo = OdooRepository(backend)

    task_name = "M-01.2 — API Spaces CRUD (UserSpace + ProjectSpace)"
    existing = repo.find_existing_task(
        1,
        build_import_key("Projet", task_name, "M-01.2"),
        task_name=task_name,
        task_code="M-01.2",
    )

    assert existing is not None
    assert existing["id"] == 12


def test_upsert_task_raises_when_write_returns_false() -> None:
    backend = _BackendStub(
        tasks=[
            {
                "id": 7,
                "name": "Task A",
                "project_id": 1,
                "x_import_key": "abc123",
            }
        ],
        write_result=False,
    )
    repo = OdooRepository(backend)

    with pytest.raises(OdooError, match="Echec de mise a jour"):
        repo.upsert_task(
            1,
            {"name": "Task A"},
            "abc123",
        )


def test_find_existing_task_uses_source_task_id_before_other_matching() -> None:
    backend = _BackendStub(
        tasks=[
            {
                "id": 42,
                "name": "Task Legacy",
                "project_id": 1,
                "x_import_key": "legacy-key",
            }
        ]
    )
    repo = OdooRepository(backend)

    existing = repo.find_existing_task(
        1,
        "new-key",
        task_name="Task Renamed",
        source_task_id=42,
    )

    assert existing is not None
    assert existing["id"] == 42


def test_get_or_create_stage_preserves_custom_stage_name() -> None:
    backend = _StageBackendStub()
    repo = OdooRepository(backend)

    stage_id = repo.get_or_create_stage(7, "spécification")

    assert stage_id == 321
    assert backend.last_stage_create == (
        "project.task.type",
        {
            "name": "spécification",
            "project_ids": [(6, 0, [7])],
        },
    )
