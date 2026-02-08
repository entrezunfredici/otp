"""Versioned mapping specifications for Odoo models and fields."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ModelMapping:
    """Model names used by the connector."""

    project: str
    task: str
    tag: str
    stage: str
    user: str


@dataclass(frozen=True)
class TaskFieldMapping:
    """Field mapping for the task model."""

    id: str = "id"
    name: str = "name"
    description: str = "description"
    project: str = "project_id"
    tags: str = "tag_ids"
    stage: str = "stage_id"
    deadline: str = "date_deadline"
    import_key: str = "x_import_key"
    estimation_candidates: tuple[str, ...] = ("planned_hours", "allocated_hours")
    owner_candidates: tuple[str, ...] = ("user_id", "user_ids")
    dependency_candidates: tuple[str, ...] = ("blocked_by", "depends_on_ids")
    field_aliases: dict[str, tuple[str, ...]] = field(default_factory=dict)


@dataclass(frozen=True)
class ProjectFieldMapping:
    """Field mapping for the project model."""

    id: str = "id"
    name: str = "name"
    field_aliases: dict[str, tuple[str, ...]] = field(default_factory=dict)


@dataclass(frozen=True)
class TagFieldMapping:
    """Field mapping for the tag model."""

    id: str = "id"
    name: str = "name"
    field_aliases: dict[str, tuple[str, ...]] = field(default_factory=dict)


@dataclass(frozen=True)
class StageFieldMapping:
    """Field mapping for the stage model."""

    id: str = "id"
    name: str = "name"
    projects_relation: str = "project_ids"
    field_aliases: dict[str, tuple[str, ...]] = field(default_factory=dict)


@dataclass(frozen=True)
class UserFieldMapping:
    """Field mapping for the user model."""

    id: str = "id"
    login: str = "login"
    name: str = "name"
    field_aliases: dict[str, tuple[str, ...]] = field(default_factory=dict)


@dataclass(frozen=True)
class OdooVersionSpec:
    """Complete mapping for an Odoo major version."""

    version_name: str
    models: ModelMapping
    task: TaskFieldMapping
    project: ProjectFieldMapping = ProjectFieldMapping()
    tag: TagFieldMapping = TagFieldMapping()
    stage: StageFieldMapping = StageFieldMapping()
    user: UserFieldMapping = UserFieldMapping()
