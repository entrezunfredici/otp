"""XML-RPC adapter for Odoo."""
import odoolib
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from odoo_task_porter.domain.errors import OdooError


@dataclass
class OdooClient:
    """Low-level XML-RPC client for Odoo."""

    url: str
    db: str
    username: str
    password: str
    server_version: str = ""
    server_major_version: int | None = None

    def __post_init__(self) -> None:
        self.server_version, self.server_major_version = self._read_server_version()
        self.uid = self.authenticate()

    def authenticate(self) -> int:
        self.client = odoolib.get_connection(
            hostname=self.url,
            protocol="jsonrpcs",
            port=443, #8069 si local
            database=self.db,
            login=self.username,
            password=self.password,
        )
        if not self.client:
            raise OdooError(
                "Authentication failed. Verifie le profil Odoo (url, db, username, password)."
            )
        return int(self.client)

    def _read_server_version(self) -> tuple[str, int | None]:
        info = self._common.version()
        if not isinstance(info, dict):
            return "", None
        raw_version = str(info.get("server_version") or "")
        major_value: int | None = None
        if raw_version:
            major_token = raw_version.split(".", 1)[0]
            if major_token.isdigit():
                major_value = int(major_token)
        return raw_version, major_value

    def get_server_major_version(self) -> int | None:
        """Return detected Odoo major version (e.g. 18, 19)."""
        return self.server_major_version

    def search_read(self, model: str, domain: list[Any], fields: list[str]) -> list[dict[str, Any]]:
        return self.client.get_model(model).search_read(domain=domain, fields=fields)

    def create(self, model: str, values: dict[str, Any]) -> int:
        return self.client.get_model(model).create(values)

    def write(self, model: str, ids: list[int], values: dict[str, Any]) -> bool:
        return self.client.get_model(model).write(ids,values)

    def delete(self, model: str, ids: list[int], values: dict[str, Any]) -> bool:
        return self.client.get_model(model).unlink(ids)

    # def fields_get(self, model: str, fields: list[str] | None = None) -> dict[str, Any]:
    #     return self.execute(model, "fields_get", fields or [], attributes=["type", "string"])
