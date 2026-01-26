"""Authentication helpers using keyring."""
from __future__ import annotations

from dataclasses import dataclass
import getpass
import os
import sys
from typing import Optional

import keyring


@dataclass(frozen=True)
class AuthResult:
    """Authentication retrieval result."""

    username: str
    password: str
    source: str


class AuthManager:
    """Manage credentials stored in keyring."""

    def __init__(self, service_prefix: str = "odoo-task-porter") -> None:
        self._service_prefix = service_prefix

    def _service_name(self, profile: str) -> str:
        return f"{self._service_prefix}:{profile}"

    def set(self, profile: str, username: str) -> None:
        password = getpass.getpass("Odoo password: ")
        if not password:
            raise ValueError("Password cannot be empty.")
        keyring.set_password(self._service_name(profile), username, password)

    def get(self, profile: str, username: str) -> AuthResult:
        password = keyring.get_password(self._service_name(profile), username)
        if password:
            return AuthResult(username=username, password=password, source="keyring")
        env_password = os.getenv("ODOO_PASSWORD")
        if env_password:
            return AuthResult(username=username, password=env_password, source="env")
        if sys.stdin.isatty():
            password = getpass.getpass("Odoo password: ")
            if password:
                return AuthResult(username=username, password=password, source="prompt")
        raise RuntimeError("Password not available (keyring/env/interactive).")

    def unset(self, profile: str, username: str) -> None:
        try:
            keyring.delete_password(self._service_name(profile), username)
        except keyring.errors.PasswordDeleteError:
            return

    def test(self, profile: str, username: str) -> AuthResult:
        return self.get(profile, username)
