"""Mapping rules between Markdown and Odoo fields."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

ALLOWED_TYPES = {"dev", "ux-ui", "devops", "infra", "qa", "sec", "doc", "produit", "research", "aide"}
ALLOWED_STATUSES = {"backlog", "todo", "in_progress", "review", "blocked", "done"}
ALLOWED_PRIORITIES = {"P0", "P1", "P2", "P3"}
ALLOWED_MOSCOW = {"Must", "Should", "Could", "Won't", "Won’t", "Wonâ€™t", "Wont"}

STATUS_TO_STAGE = {
    "backlog": "Backlog",
    "todo": "To Do",
    "in_progress": "In Progress",
    "review": "Review",
    "blocked": "Blocked",
    "done": "Done",
}

STAGE_TO_STATUS = {value: key for key, value in STATUS_TO_STAGE.items()}

DEFAULT_ESTIMATION_MAP = {
    "XS": 2,
    "S": 4,
    "M": 8,
    "L": 16,
    "XL": 32,
}


@dataclass(frozen=True)
class TagMapping:
    """Container for tag mapping prefixes."""

    type_prefix: str = "type_"
    priority_prefix: str = "priority_"
    moscow_prefix: str = "moscow_"


def stage_name_to_status(value: str) -> str:
    """Convert a known Odoo stage label to a canonical status, else preserve it."""
    normalized = value.strip()
    if not normalized:
        return ""
    return STAGE_TO_STATUS.get(normalized, normalized)


def status_to_stage_name(value: str) -> str:
    """Convert a canonical status to an Odoo stage label, else preserve it."""
    normalized = value.strip()
    if not normalized:
        return ""
    return STATUS_TO_STAGE.get(normalized, normalized)


def is_supported_status(value: str) -> bool:
    """Allow canonical statuses and custom Odoo stage names."""
    return bool(value.strip())


def estimation_to_hours(value: str, mapping: Dict[str, int] | None = None) -> float | None:
    """Convert estimation string to planned hours."""
    mapping = mapping or DEFAULT_ESTIMATION_MAP
    if not value:
        return None
    raw = value.strip()
    if raw in mapping:
        return float(mapping[raw])
    if raw.endswith("h") and raw[:-1].isdigit():
        return float(raw[:-1])
    if raw.endswith("j") and raw[:-1].isdigit():
        return float(raw[:-1]) * 8
    return None


def hours_to_estimation(hours: float | None) -> str:
    """Convert planned hours back to estimation string."""
    if hours is None:
        return ""
    if hours % 8 == 0:
        days = int(hours / 8)
        return f"{days}j"
    return f"{int(hours)}h"
