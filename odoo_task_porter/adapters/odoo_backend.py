"""Backend protocol for Odoo data access."""
from __future__ import annotations

from typing import Any, Protocol


class OdooBackend(Protocol):
    """Contract required by repository operations."""

    def search_read(self, model: str, domain: list[Any], fields: list[str]) -> list[dict[str, Any]]:
        ...

    def create(self, model: str, values: dict[str, Any]) -> int:
        ...

    def write(self, model: str, ids: list[int], values: dict[str, Any]) -> bool:
        ...

    def fields_get(self, model: str, fields: list[str] | None = None) -> dict[str, Any]:
        ...

    def get_server_major_version(self) -> int | None:
        ...
