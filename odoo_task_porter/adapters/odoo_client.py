"""JSON-RPC adapter for Odoo using odoolib."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse
import odoolib
from odoo_task_porter.domain.errors import OdooError


@dataclass
class OdooClient:
    """Low-level Odoo client implemented with odoolib."""

    url: str
    db: str
    username: str
    password: str
    server_version: str = ""
    server_major_version: int | None = None

    def __post_init__(self) -> None:
        if odoolib is None:
            raise OdooError(
                "Missing dependency 'odoo-client-lib'. Install requirements before using OdooClient."
            )
        hostname, protocol, port = self._parse_connection_url(self.url)
        try:
            self.client = odoolib.get_connection(
                hostname=hostname,
                protocol=protocol,
                port=port,
                database=self.db,
                login=self.username,
                password=self.password,
            )
        except Exception as exc:  # noqa: BLE001
            raise OdooError(
                "Authentication failed. Check Odoo profile (url, db, username, password)."
            ) from exc
        if not self.client:
            raise OdooError(
                "Authentication failed. Check Odoo profile (url, db, username, password)."
            )
        self.server_version, self.server_major_version = self._read_server_version()

    @staticmethod
    def _parse_connection_url(raw_url: str) -> tuple[str, str, int]:
        normalized = raw_url if "://" in raw_url else f"https://{raw_url}"
        parsed = urlparse(normalized)
        scheme = parsed.scheme.lower() if parsed.scheme else "https"
        hostname = parsed.hostname or raw_url
        protocol = "jsonrpcs" if scheme == "https" else "jsonrpc"
        default_port = 443 if scheme == "https" else 80
        return hostname, protocol, parsed.port or default_port

    def _read_server_version(self) -> tuple[str, int | None]:
        info: Any = None
        get_service = getattr(self.client, "get_service", None)
        if callable(get_service):
            try:
                common = get_service("common")
                version_method = getattr(common, "version", None)
                if callable(version_method):
                    info = version_method()
            except Exception:  # noqa: BLE001
                info = None
        if not isinstance(info, dict):
            version_method = getattr(self.client, "version", None)
            if callable(version_method):
                try:
                    info = version_method()
                except Exception:  # noqa: BLE001
                    info = None

        raw_version = ""
        if isinstance(info, dict):
            raw_version = str(info.get("server_version") or "")
        if not raw_version:
            direct_version = getattr(self.client, "server_version", "")
            raw_version = str(direct_version or "")

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
        return int(self.client.get_model(model).create(values))

    def write(self, model: str, ids: list[int], values: dict[str, Any]) -> bool:
        return bool(self.client.get_model(model).write(ids, values))

    def delete(self, model: str, ids: list[int]) -> bool:
        return bool(self.client.get_model(model).unlink(ids))

    def fields_get(self, model: str, fields: list[str] | None = None) -> dict[str, Any]:
        model_proxy = self.client.get_model(model)
        getter = getattr(model_proxy, "fields_get", None)
        if not callable(getter):
            raise OdooError(f"Model '{model}' does not provide fields_get via odoolib.")

        requested = list(fields or [])
        attributes = ["type", "string"]
        attempts = [
            ((requested,), {"attributes": attributes}),
            ((), {"fields": requested, "attributes": attributes}),
            ((requested, attributes), {}),
            ((), {"attributes": attributes}),
            ((requested,), {}),
            ((), {}),
        ]
        result: Any = {}
        for args, kwargs in attempts:
            try:
                result = getter(*args, **kwargs)
                break
            except TypeError:
                continue

        if not isinstance(result, dict):
            return {}
        if requested:
            return {name: metadata for name, metadata in result.items() if name in requested}
        return result
