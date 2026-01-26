"""Validation rules."""
from __future__ import annotations

from datetime import date
from typing import Iterable

from odoo_task_porter.domain.errors import ValidationError
from odoo_task_porter.domain.models import TaskMetadata
from odoo_task_porter.transform.mapping import (
    ALLOWED_MOSCOW,
    ALLOWED_PRIORITIES,
    ALLOWED_STATUSES,
    ALLOWED_TYPES,
)


def validate_metadata(metadata: TaskMetadata) -> None:
    """Validate metadata values."""
    errors: list[str] = []
    if metadata.task_type not in ALLOWED_TYPES:
        errors.append(f"Type invalide: {metadata.task_type}")
    if metadata.status not in ALLOWED_STATUSES:
        errors.append(f"Statut invalide: {metadata.status}")
    if metadata.priority not in ALLOWED_PRIORITIES:
        errors.append(f"Priorité invalide: {metadata.priority}")
    if metadata.moscow not in ALLOWED_MOSCOW:
        errors.append(f"MoSCoW invalide: {metadata.moscow}")
    if metadata.deadline and not isinstance(metadata.deadline, date):
        errors.append("Deadline invalide")
    if errors:
        raise ValidationError(", ".join(errors))


def require_fields(values: dict[str, str], required: Iterable[str]) -> None:
    missing = [key for key in required if key not in values or not values[key]]
    if missing:
        raise ValidationError(f"Champs manquants: {', '.join(missing)}")
