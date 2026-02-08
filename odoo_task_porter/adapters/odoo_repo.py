"""Repository helpers for Odoo operations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from odoo_task_porter.adapters.odoo_backend import OdooBackend
from odoo_task_porter.domain.errors import OdooError
from odoo_task_porter.transform.mapping import STATUS_TO_STAGE
from odoo_task_porter.versions import resolve_version_spec
from odoo_task_porter.versions.spec import OdooVersionSpec


@dataclass
class OdooRepository:
    """Higher-level Odoo repository operations."""

    client: OdooBackend

    def get_server_major_version(self) -> int | None:
        """Return detected Odoo major version when backend provides it."""
        getter = getattr(self.client, "get_server_major_version", None)
        if callable(getter):
            value = getter()
            if isinstance(value, int):
                return value
        return None

    def get_version_spec(self) -> OdooVersionSpec:
        """Return resolved mapping specification for current Odoo version."""
        return resolve_version_spec(self.get_server_major_version())

    def resolve_task_fields(self) -> dict[str, str | None]:
        """Resolve task field names from the version mapping + available fields."""
        resolved_aliases = self.resolve_task_field_aliases()
        spec = self.get_version_spec()
        return {
            "id": spec.task.id,
            "name": spec.task.name,
            "description": spec.task.description,
            "project": spec.task.project,
            "tags": spec.task.tags,
            "stage": spec.task.stage,
            "deadline": resolved_aliases.get("deadline"),
            "import_key": resolved_aliases.get("import_key"),
            "estimation_hours": resolved_aliases.get("planned_hours"),
            "owner": resolved_aliases.get("owner"),
        }

    def resolve_task_field_aliases(self) -> dict[str, str | None]:
        """Resolve all configured task field aliases for current Odoo version."""
        spec = self.get_version_spec()
        configured_aliases = dict(spec.task.field_aliases)
        configured_aliases.setdefault("owner", spec.task.owner_candidates)
        configured_aliases.setdefault("planned_hours", spec.task.estimation_candidates)
        configured_aliases.setdefault("dependencies", spec.task.dependency_candidates)
        configured_aliases.setdefault("deadline", (spec.task.deadline,))
        configured_aliases.setdefault("import_key", (spec.task.import_key,))
        return self._resolve_model_field_aliases(spec.models.task, configured_aliases)

    def resolve_project_field_aliases(self) -> dict[str, str | None]:
        """Resolve all configured project field aliases."""
        spec = self.get_version_spec()
        configured_aliases = dict(spec.project.field_aliases)
        configured_aliases.setdefault("id", (spec.project.id,))
        configured_aliases.setdefault("name", (spec.project.name,))
        return self._resolve_model_field_aliases(spec.models.project, configured_aliases)

    def resolve_tag_field_aliases(self) -> dict[str, str | None]:
        """Resolve all configured tag field aliases."""
        spec = self.get_version_spec()
        configured_aliases = dict(spec.tag.field_aliases)
        configured_aliases.setdefault("id", (spec.tag.id,))
        configured_aliases.setdefault("name", (spec.tag.name,))
        return self._resolve_model_field_aliases(spec.models.tag, configured_aliases)

    def resolve_stage_field_aliases(self) -> dict[str, str | None]:
        """Resolve all configured stage field aliases."""
        spec = self.get_version_spec()
        configured_aliases = dict(spec.stage.field_aliases)
        configured_aliases.setdefault("id", (spec.stage.id,))
        configured_aliases.setdefault("name", (spec.stage.name,))
        configured_aliases.setdefault("projects_relation", (spec.stage.projects_relation,))
        return self._resolve_model_field_aliases(spec.models.stage, configured_aliases)

    def resolve_user_field_aliases(self) -> dict[str, str | None]:
        """Resolve all configured user field aliases."""
        spec = self.get_version_spec()
        configured_aliases = dict(spec.user.field_aliases)
        configured_aliases.setdefault("id", (spec.user.id,))
        configured_aliases.setdefault("login", (spec.user.login,))
        configured_aliases.setdefault("name", (spec.user.name,))
        return self._resolve_model_field_aliases(spec.models.user, configured_aliases)

    def get_project_id(self, project_name: str) -> int:
        spec = self.get_version_spec()
        project_fields = self.resolve_project_field_aliases()
        project_name_field = self._require_alias(project_fields, "name", spec.models.project)
        project_id_field = self._require_alias(project_fields, "id", spec.models.project)
        results = self.client.search_read(
            spec.models.project,
            [[project_name_field, "=", project_name]],
            [project_id_field, project_name_field],
        )
        if not results:
            raise OdooError(f"Project '{project_name}' not found.")
        return int(results[0][project_id_field])

    def ensure_import_key_field(self, import_key_field: str | None = None) -> None:
        spec = self.get_version_spec()
        target_field = import_key_field or spec.task.import_key
        fields = self.client.fields_get(spec.models.task, [target_field])
        if target_field not in fields:
            raise OdooError(
                f"Le champ custom {target_field} est requis sur {spec.models.task}."
            )

    def find_task_by_import_key(self, project_id: int, import_key: str) -> dict[str, Any] | None:
        spec = self.get_version_spec()
        task_fields = self.resolve_task_fields()
        import_key_field = task_fields["import_key"]
        if import_key_field is None:
            return None
        results = self.client.search_read(
            spec.models.task,
            [
                [import_key_field, "=", import_key],
                [task_fields["project"], "=", project_id],
            ],
            [task_fields["id"], task_fields["name"]],
        )
        return results[0] if results else None

    def upsert_task(self, project_id: int, values: dict[str, Any], import_key: str) -> int:
        spec = self.get_version_spec()
        task_fields = self.resolve_task_fields()
        existing = self.find_task_by_import_key(project_id, import_key)
        if existing:
            self.client.write(spec.models.task, [int(existing[task_fields["id"]])], values)
            return int(existing[task_fields["id"]])
        return self.client.create(spec.models.task, values)

    def find_tag_id(self, name: str) -> int | None:
        spec = self.get_version_spec()
        tag_fields = self.resolve_tag_field_aliases()
        tag_name_field = self._require_alias(tag_fields, "name", spec.models.tag)
        tag_id_field = self._require_alias(tag_fields, "id", spec.models.tag)
        records = self.client.search_read(
            spec.models.tag,
            [[tag_name_field, "=", name]],
            [tag_id_field],
        )
        if not records:
            return None
        return int(records[0][tag_id_field])

    def get_or_create_tag(self, name: str) -> int:
        spec = self.get_version_spec()
        tag_fields = self.resolve_tag_field_aliases()
        tag_name_field = self._require_alias(tag_fields, "name", spec.models.tag)
        existing_id = self.find_tag_id(name)
        if existing_id is not None:
            return existing_id
        return self.client.create(spec.models.tag, {tag_name_field: name})

    def get_or_create_stage(self, project_id: int, status: str) -> int:
        spec = self.get_version_spec()
        stage_fields = self.resolve_stage_field_aliases()
        stage_name_field = self._require_alias(stage_fields, "name", spec.models.stage)
        stage_id_field = self._require_alias(stage_fields, "id", spec.models.stage)
        stage_projects_field = self._require_alias(
            stage_fields, "projects_relation", spec.models.stage
        )
        stage_name = STATUS_TO_STAGE.get(status, status)
        results = self.client.search_read(
            spec.models.stage,
            [
                [stage_name_field, "=", stage_name],
                [stage_projects_field, "in", [project_id]],
            ],
            [stage_id_field],
        )
        if results:
            return int(results[0][stage_id_field])
        return self.client.create(
            spec.models.stage,
            {
                stage_name_field: stage_name,
                stage_projects_field: [(6, 0, [project_id])],
            },
        )

    def find_user(self, owner: str) -> int | None:
        spec = self.get_version_spec()
        user_fields = self.resolve_user_field_aliases()
        user_id_field = self._require_alias(user_fields, "id", spec.models.user)
        user_login_field = self._require_alias(user_fields, "login", spec.models.user)
        user_name_field = self._require_alias(user_fields, "name", spec.models.user)
        if "@" in owner and "." in owner:
            results = self.client.search_read(
                spec.models.user,
                [[user_login_field, "=", owner]],
                [user_id_field, user_login_field],
            )
            if results:
                return int(results[0][user_id_field])
        results = self.client.search_read(
            spec.models.user,
            [[user_name_field, "ilike", owner]],
            [user_id_field],
        )
        if results:
            return int(results[0][user_id_field])
        return None

    def fields(self, model: str, field_names: Iterable[str]) -> dict[str, Any]:
        return self.client.fields_get(model, list(field_names))

    def find_tasks(self, domain: list[Any], fields: list[str]) -> list[dict[str, Any]]:
        spec = self.get_version_spec()
        return self.client.search_read(spec.models.task, domain, fields)

    def read_project_tags(self, tag_ids: list[int]) -> list[str]:
        if not tag_ids:
            return []
        spec = self.get_version_spec()
        tag_fields = self.resolve_tag_field_aliases()
        tag_id_field = self._require_alias(tag_fields, "id", spec.models.tag)
        tag_name_field = self._require_alias(tag_fields, "name", spec.models.tag)
        records = self.client.search_read(
            spec.models.tag,
            [[tag_id_field, "in", tag_ids]],
            [tag_name_field],
        )
        return [str(record[tag_name_field]) for record in records if record.get(tag_name_field)]

    def read_user_names(self, user_ids: list[int]) -> list[str]:
        if not user_ids:
            return []
        spec = self.get_version_spec()
        user_fields = self.resolve_user_field_aliases()
        user_id_field = self._require_alias(user_fields, "id", spec.models.user)
        user_name_field = self._require_alias(user_fields, "name", spec.models.user)
        records = self.client.search_read(
            spec.models.user,
            [[user_id_field, "in", user_ids]],
            [user_name_field],
        )
        return [str(record[user_name_field]) for record in records if record.get(user_name_field)]

    def supports_dependency_field(self) -> str | None:
        spec = self.get_version_spec()
        fields = self.client.fields_get(spec.models.task, [])
        for candidate in spec.task.dependency_candidates:
            if candidate in fields:
                return candidate
        return None

    def add_dependencies(self, task_id: int, dependency_ids: list[int], field_name: str) -> None:
        if not dependency_ids:
            return
        spec = self.get_version_spec()
        self.client.write(spec.models.task, [task_id], {field_name: [(6, 0, dependency_ids)]})

    def _resolve_model_field_aliases(
        self,
        model: str,
        configured_aliases: dict[str, tuple[str, ...]],
    ) -> dict[str, str | None]:
        available = self.client.fields_get(model, [])
        available_names = set(available.keys())
        aliases: dict[str, str | None] = {}
        for alias, candidates in configured_aliases.items():
            aliases[alias] = self._pick_existing_field(available_names, list(candidates))
        return aliases

    @staticmethod
    def _require_alias(
        aliases: dict[str, str | None],
        alias_name: str,
        model: str,
    ) -> str:
        value = aliases.get(alias_name)
        if value:
            return value
        raise OdooError(
            f"Champ requis non resolu pour alias '{alias_name}' sur le modele '{model}'."
        )

    @staticmethod
    def _pick_existing_field(available: set[str], candidates: list[str]) -> str | None:
        for candidate in candidates:
            if candidate in available:
                return candidate
        return None
