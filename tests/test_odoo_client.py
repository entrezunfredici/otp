from __future__ import annotations
from types import SimpleNamespace
import httpx
from odoolib.rpc import AuthenticationError as OdooAuthenticationError
from odoolib.tools import JsonRPCException
import pytest
from odoo_task_porter.adapters import odoo_client as client_module
from odoo_task_porter.domain.errors import OdooError


class _FakeOdooLib:
    def __init__(self, connection: object | None = None, exc: Exception | None = None) -> None:
        self.connection = connection
        self.exc = exc
        self.calls: list[dict[str, object]] = []

    def get_connection(self, **kwargs):
        self.calls.append(kwargs)
        if self.exc:
            raise self.exc
        return self.connection


class _ConnectionWithCommonService:
    def __init__(self, version_info: dict[str, str]) -> None:
        self._version_info = version_info

    def get_service(self, name: str):
        assert name == "common"
        return SimpleNamespace(version=lambda: self._version_info)

    def get_model(self, model: str):
        raise AssertionError(f"unexpected model access: {model}")


class _ConnectionWithVersionMethod:
    def __init__(self, version_info: dict[str, str]) -> None:
        self._version_info = version_info

    def version(self):
        return self._version_info

    def get_model(self, model: str):
        raise AssertionError(f"unexpected model access: {model}")


class _ConnectionWithServerVersionAttr:
    def __init__(self, server_version: str) -> None:
        self.server_version = server_version

    def get_model(self, model: str):
        raise AssertionError(f"unexpected model access: {model}")


class _ConnectionWithModel:
    def __init__(self, model) -> None:
        self._model = model

    def get_service(self, name: str):
        assert name == "common"
        return SimpleNamespace(version=lambda: {"server_version": "19.0+e"})

    def get_model(self, model_name: str):
        assert model_name == "project.task"
        return self._model


class _FieldsGetKeywordOnlyModel:
    def __init__(self) -> None:
        self.last_fields: list[str] | None = None
        self.last_attributes: list[str] | None = None

    def fields_get(self, *, fields: list[str], attributes: list[str]) -> dict[str, dict[str, str]]:
        self.last_fields = fields
        self.last_attributes = attributes
        return {
            "name": {"type": "char", "string": "Name"},
            "date_deadline": {"type": "date", "string": "Deadline"},
        }


class _FieldsGetAttributesOnlyModel:
    def fields_get(self, *, attributes: list[str]) -> dict[str, dict[str, str]]:
        assert attributes == ["type", "string"]
        return {
            "name": {"type": "char", "string": "Name"},
            "date_deadline": {"type": "date", "string": "Deadline"},
        }


class _ModelWithoutFieldsGet:
    pass


class _TimeoutModel:
    def __init__(self) -> None:
        self.calls = 0

    def search_read(self, *, domain, fields):
        self.calls += 1
        raise httpx.ConnectTimeout("timed out")


class _AuthFailureModel:
    def search_read(self, *, domain, fields):
        raise OdooAuthenticationError("bad credentials")


class _JsonRpcFailureModel:
    def search_read(self, *, domain, fields):
        raise JsonRPCException(
            {
                "message": "Odoo Server Error",
                "data": {"message": "Access denied by ACL"},
            }
        )


def test_init_raises_when_odoolib_dependency_is_missing(monkeypatch) -> None:
    monkeypatch.setattr(client_module, "odoolib", None)

    with pytest.raises(OdooError, match="Missing dependency"):
        client_module.OdooClient("https://demo.odoo.com", "db", "user", "pwd")


def test_read_server_version_from_common_service(monkeypatch) -> None:
    fake_lib = _FakeOdooLib(
        connection=_ConnectionWithCommonService({"server_version": "19.0+e"})
    )
    monkeypatch.setattr(client_module, "odoolib", fake_lib)

    client = client_module.OdooClient("https://demo.odoo.com", "db", "user", "pwd")

    assert client.server_version == "19.0+e"
    assert client.server_major_version == 19
    assert fake_lib.calls[0]["hostname"] == "demo.odoo.com"
    assert fake_lib.calls[0]["protocol"] == "jsonrpcs"
    assert fake_lib.calls[0]["port"] == 443


def test_read_server_version_from_client_version_method(monkeypatch) -> None:
    fake_lib = _FakeOdooLib(
        connection=_ConnectionWithVersionMethod({"server_version": "18.3"})
    )
    monkeypatch.setattr(client_module, "odoolib", fake_lib)

    client = client_module.OdooClient("http://localhost:8069", "db", "user", "pwd")

    assert client.server_version == "18.3"
    assert client.server_major_version == 18
    assert fake_lib.calls[0]["hostname"] == "localhost"
    assert fake_lib.calls[0]["protocol"] == "jsonrpc"
    assert fake_lib.calls[0]["port"] == 8069


def test_read_server_version_from_server_version_attribute(monkeypatch) -> None:
    fake_lib = _FakeOdooLib(connection=_ConnectionWithServerVersionAttr("17.0+e"))
    monkeypatch.setattr(client_module, "odoolib", fake_lib)

    client = client_module.OdooClient("demo.odoo.com", "db", "user", "pwd")

    assert client.server_version == "17.0+e"
    assert client.server_major_version == 17


def test_fields_get_supports_keyword_only_signature(monkeypatch) -> None:
    model = _FieldsGetKeywordOnlyModel()
    fake_lib = _FakeOdooLib(connection=_ConnectionWithModel(model))
    monkeypatch.setattr(client_module, "odoolib", fake_lib)
    client = client_module.OdooClient("https://demo.odoo.com", "db", "user", "pwd")

    fields = client.fields_get("project.task", ["date_deadline"])

    assert fields == {"date_deadline": {"type": "date", "string": "Deadline"}}
    assert model.last_fields == ["date_deadline"]
    assert model.last_attributes == ["type", "string"]


def test_fields_get_filters_results_when_api_does_not_accept_fields(monkeypatch) -> None:
    model = _FieldsGetAttributesOnlyModel()
    fake_lib = _FakeOdooLib(connection=_ConnectionWithModel(model))
    monkeypatch.setattr(client_module, "odoolib", fake_lib)
    client = client_module.OdooClient("https://demo.odoo.com", "db", "user", "pwd")

    fields = client.fields_get("project.task", ["name"])

    assert fields == {"name": {"type": "char", "string": "Name"}}


def test_fields_get_raises_when_model_has_no_fields_get(monkeypatch) -> None:
    fake_lib = _FakeOdooLib(connection=_ConnectionWithModel(_ModelWithoutFieldsGet()))
    monkeypatch.setattr(client_module, "odoolib", fake_lib)
    client = client_module.OdooClient("https://demo.odoo.com", "db", "user", "pwd")

    with pytest.raises(OdooError, match="does not provide fields_get"):
        client.fields_get("project.task", ["name"])


def test_init_raises_when_connection_returns_falsy(monkeypatch) -> None:
    fake_lib = _FakeOdooLib(connection=None)
    monkeypatch.setattr(client_module, "odoolib", fake_lib)

    with pytest.raises(OdooError, match="Authentication failed"):
        client_module.OdooClient("https://demo.odoo.com", "db", "user", "pwd")


def test_init_raises_when_odoolib_connection_fails(monkeypatch) -> None:
    fake_lib = _FakeOdooLib(exc=RuntimeError("boom"))
    monkeypatch.setattr(client_module, "odoolib", fake_lib)

    with pytest.raises(OdooError, match="Authentication failed"):
        client_module.OdooClient("https://demo.odoo.com", "db", "user", "pwd")


def test_search_read_wraps_connect_timeout_with_retry(monkeypatch) -> None:
    model = _TimeoutModel()
    fake_lib = _FakeOdooLib(connection=_ConnectionWithModel(model))
    monkeypatch.setattr(client_module, "odoolib", fake_lib)
    client = client_module.OdooClient("https://demo.odoo.com", "db", "user", "pwd")

    with pytest.raises(OdooError, match="Connection timed out"):
        client.search_read("project.task", [], ["name"])

    assert model.calls == 2


def test_search_read_wraps_authentication_errors(monkeypatch) -> None:
    fake_lib = _FakeOdooLib(connection=_ConnectionWithModel(_AuthFailureModel()))
    monkeypatch.setattr(client_module, "odoolib", fake_lib)
    client = client_module.OdooClient("https://demo.odoo.com", "db", "user", "pwd")

    with pytest.raises(OdooError, match="Authentication failed"):
        client.search_read("project.task", [], ["name"])


def test_search_read_wraps_jsonrpc_errors(monkeypatch) -> None:
    fake_lib = _FakeOdooLib(connection=_ConnectionWithModel(_JsonRpcFailureModel()))
    monkeypatch.setattr(client_module, "odoolib", fake_lib)
    client = client_module.OdooClient("https://demo.odoo.com", "db", "user", "pwd")

    with pytest.raises(OdooError, match="Access denied by ACL"):
        client.search_read("project.task", [], ["name"])
