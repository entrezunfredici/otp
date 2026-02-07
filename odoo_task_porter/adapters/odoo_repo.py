"""Repository helpers for Odoo operations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from odoo_task_porter.adapters.odoo_backend import OdooBackend
from odoo_task_porter.domain.errors import OdooError
from odoo_task_porter.transform.mapping import STATUS_TO_STAGE


@dataclass
class OdooRepository:
    """Higher-level Odoo repository operations."""

    client: OdooBackend

    def get_project_id(self, project_name: str) -> int:
        results = self.client.search_read(
            "project.project", [["name", "=", project_name]], ["id", "name"]
        )
        if not results:
            raise OdooError(f"Project '{project_name}' not found.")
        return int(results[0]["id"])

    def ensure_import_key_field(self) -> None:
        fields = self.client.fields_get("project.task", ["x_import_key"])
        if "x_import_key" not in fields:
            raise OdooError("Le champ custom x_import_key est requis sur project.task.")

    def find_task_by_import_key(self, project_id: int, import_key: str) -> dict[str, Any] | None:
        results = self.client.search_read(
            "project.task",
            [["x_import_key", "=", import_key], ["project_id", "=", project_id]],
            ["id", "name"],
        )
        return results[0] if results else None

    def upsert_task(self, project_id: int, values: dict[str, Any], import_key: str) -> int:
        existing = self.find_task_by_import_key(project_id, import_key)
        if existing:
            self.client.write("project.task", [int(existing["id"])], values)
            return int(existing["id"])
        return self.client.create("project.task", values)

    def get_or_create_tag(self, name: str) -> int:
        existing = self.client.search_read("project.tags", [["name", "=", name]], ["id"])
        if existing:
            return int(existing[0]["id"])
        return self.client.create("project.tags", {"name": name})

    def get_or_create_stage(self, project_id: int, status: str) -> int:
        stage_name = STATUS_TO_STAGE.get(status, status)
        results = self.client.search_read(
            "project.task.type",
            [["name", "=", stage_name], ["project_ids", "in", [project_id]]],
            ["id"],
        )
        if results:
            return int(results[0]["id"])
        return self.client.create(
            "project.task.type", {"name": stage_name, "project_ids": [(6, 0, [project_id])]}
        )

    def find_user(self, owner: str) -> int | None:
        if "@" in owner and "." in owner:
            results = self.client.search_read(
                "res.users", [["login", "=", owner]], ["id", "login"]
            )
            if results:
                return int(results[0]["id"])
        results = self.client.search_read("res.users", [["name", "ilike", owner]], ["id"])
        if results:
            return int(results[0]["id"])
        return None

    def fields(self, model: str, field_names: Iterable[str]) -> dict[str, Any]:
        return self.client.fields_get(model, list(field_names))

    def find_tasks(self, domain: list[Any], fields: list[str]) -> list[dict[str, Any]]:
        return self.client.search_read("project.task", domain, fields)

    def read_project_tags(self, tag_ids: list[int]) -> list[str]:
        if not tag_ids:
            return []
        records = self.client.search_read("project.tags", [["id", "in", tag_ids]], ["name"])
        return [record["name"] for record in records]

    def supports_dependency_field(self) -> str | None:
        fields = self.client.fields_get("project.task", [])
        for candidate in ("blocked_by", "depends_on_ids"):
            if candidate in fields:
                return candidate
        return None

    def add_dependencies(self, task_id: int, dependency_ids: list[int], field_name: str) -> None:
        if not dependency_ids:
            return
        self.client.write("project.task", [task_id], {field_name: [(6, 0, dependency_ids)]})
