"""XML-RPC adapter for Odoo."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from xmlrpc.client import ServerProxy

from odoo_task_porter.domain.errors import OdooError


@dataclass
class OdooClient:
    """Low-level XML-RPC client for Odoo."""

    url: str
    db: str
    username: str
    password: str

    def __post_init__(self) -> None:
        self._common = ServerProxy(f"{self.url}/xmlrpc/2/common")
        self._object = ServerProxy(f"{self.url}/xmlrpc/2/object")
        self.uid = self.authenticate()

    def authenticate(self) -> int:
        uid = self._common.authenticate(self.db, self.username, self.password, {})
        if not uid:
            raise OdooError("Authentication failed.")
        return int(uid)

    def execute(self, model: str, method: str, *args: Any, **kwargs: Any) -> Any:
        return self._object.execute_kw(self.db, self.uid, self.password, model, method, list(args), kwargs)

    def search_read(self, model: str, domain: list[Any], fields: list[str]) -> list[dict[str, Any]]:
        return self.execute(model, "search_read", domain, {"fields": fields})

    def create(self, model: str, values: dict[str, Any]) -> int:
        return int(self.execute(model, "create", values))

    def write(self, model: str, ids: list[int], values: dict[str, Any]) -> bool:
        return bool(self.execute(model, "write", ids, values))

    def fields_get(self, model: str, fields: list[str] | None = None) -> dict[str, Any]:
        return self.execute(model, "fields_get", fields or [], {"attributes": ["type", "string"]})
