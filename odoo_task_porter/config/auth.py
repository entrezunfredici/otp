"""Authentication helpers using keyring."""
from __future__ import annotations

from dataclasses import dataclass
import getpass, json, os, sys, keyring
from typing import Optional


@dataclass(frozen=True)
class AuthResult:
    """Authentication retrieval result."""

    url: str
    db: str
    username: str
    password: str
    source: str


class AuthManager:
    """Manage credentials stored in keyring."""

    _KEY_URL = "__url__"
    _KEY_DB = "__db__"
    _KEY_USERNAME = "__username__"
    _KEY_PASSWORD = "__password__"
    _REGISTRY_SERVICE = "__registry__"
    _REGISTRY_KEY = "__profiles__"

    def __init__(self, service_prefix: str = "odoo-task-porter") -> None:
        self._service_prefix = service_prefix

    def _service_name(self, profile: str) -> str:
        return f"{self._service_prefix}:{profile}"

    def set(
        self,
        profile: str,
        username: str | None = None,
        url: str | None = None,
        db: str | None = None,
        password: str | None = None,
    ) -> None:
        username_value = (username or "").strip() or self._prompt_required("Odoo username (email): ")
        url_value = (url or "").strip() or self._prompt_required("Odoo URL: ")
        db_value = (db or "").strip() or self._prompt_required("Odoo database: ")
        password_value = (password or "").strip() or getpass.getpass("Odoo password: ")
        if not password_value:
            raise ValueError("Password cannot be empty.")
        service = self._service_name(profile)
        keyring.set_password(service, self._KEY_USERNAME, username_value)
        keyring.set_password(service, self._KEY_URL, url_value)
        keyring.set_password(service, self._KEY_DB, db_value)
        keyring.set_password(service, self._KEY_PASSWORD, password_value)
        self._add_profile_to_registry(profile)

    def get(
        self,
        profile: str,
        fallback_username: Optional[str] = None,
        fallback_url: Optional[str] = None,
        fallback_db: Optional[str] = None,
    ) -> AuthResult:
        service = self._service_name(profile)
        sources: list[str] = []

        username = keyring.get_password(service, self._KEY_USERNAME)
        if username:
            sources.append("keyring")
        else:
            username = (fallback_username or "").strip()
            if username:
                sources.append("config")

        url = keyring.get_password(service, self._KEY_URL)
        if url:
            if "keyring" not in sources:
                sources.append("keyring")
        else:
            url = (fallback_url or "").strip()
            if url and "config" not in sources:
                sources.append("config")

        db = keyring.get_password(service, self._KEY_DB)
        if db:
            if "keyring" not in sources:
                sources.append("keyring")
        else:
            db = (fallback_db or "").strip()
            if db and "config" not in sources:
                sources.append("config")

        password = keyring.get_password(service, self._KEY_PASSWORD)
        if not password and username:
            # Backward compatibility for older entries where password used username as key.
            password = keyring.get_password(service, username)
        if password:
            if "keyring" not in sources:
                sources.append("keyring")
        env_password = os.getenv("ODOO_PASSWORD")
        if not password and env_password:
            password = env_password
            sources.append("env")

        if sys.stdin.isatty():
            if not username:
                username = self._prompt_optional("Odoo username (email): ")
            if not url:
                url = self._prompt_optional("Odoo URL: ")
            if not db:
                db = self._prompt_optional("Odoo database: ")
            if not password:
                password = getpass.getpass("Odoo password: ")
                if password and "prompt" not in sources:
                    sources.append("prompt")

        missing: list[str] = []
        if not url:
            missing.append("url")
        if not db:
            missing.append("db")
        if not username:
            missing.append("username")
        if not password:
            missing.append("password")
        if missing:
            missing_text = ", ".join(missing)
            raise RuntimeError(
                f"Credentials not available for profile '{profile}' (missing: {missing_text})."
            )
        return AuthResult(
            url=url,
            db=db,
            username=username,
            password=password,
            source="+".join(sources) if sources else "unknown",
        )

    def unset(self, profile: str, username: Optional[str] = None) -> None:
        service = self._service_name(profile)
        legacy_username = username or keyring.get_password(service, self._KEY_USERNAME)
        keys = [self._KEY_URL, self._KEY_DB, self._KEY_USERNAME, self._KEY_PASSWORD]
        if legacy_username:
            keys.append(legacy_username)
        for key in keys:
            try:
                keyring.delete_password(service, key)
            except keyring.errors.PasswordDeleteError:
                continue
        self._remove_profile_from_registry(profile)

    def list_profiles(self) -> list[str]:
        """List profiles known by auth set/unset operations."""
        profiles = set(self._load_registry())
        profiles.update(self._discover_profiles_from_keyring())
        return sorted(profiles)

    def test(
        self,
        profile: str,
        fallback_username: Optional[str] = None,
        fallback_url: Optional[str] = None,
        fallback_db: Optional[str] = None,
    ) -> AuthResult:
        return self.get(profile, fallback_username, fallback_url, fallback_db)

    def _prompt_required(self, message: str) -> str:
        value = input(message).strip()
        if not value:
            raise ValueError(f"{message.strip(': ')} cannot be empty.")
        return value

    def _prompt_optional(self, message: str) -> str:
        return input(message).strip()

    def _registry_service_name(self) -> str:
        return f"{self._service_prefix}:{self._REGISTRY_SERVICE}"

    def _load_registry(self) -> list[str]:
        raw = keyring.get_password(self._registry_service_name(), self._REGISTRY_KEY)
        if not raw:
            return []
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return []
        if not isinstance(data, list):
            return []
        return [str(item).strip() for item in data if str(item).strip()]

    def _save_registry(self, profiles: list[str]) -> None:
        unique_profiles = sorted(set(profiles))
        if not unique_profiles:
            try:
                keyring.delete_password(self._registry_service_name(), self._REGISTRY_KEY)
            except keyring.errors.PasswordDeleteError:
                pass
            return
        payload = json.dumps(unique_profiles)
        keyring.set_password(self._registry_service_name(), self._REGISTRY_KEY, payload)

    def _add_profile_to_registry(self, profile: str) -> None:
        existing = self._load_registry()
        existing.append(profile)
        self._save_registry(existing)

    def _remove_profile_from_registry(self, profile: str) -> None:
        existing = self._load_registry()
        remaining = [item for item in existing if item != profile]
        self._save_registry(remaining)

    def _discover_profiles_from_keyring(self) -> list[str]:
        """Best-effort profile discovery from backend entries (Windows)."""
        try:
            import ctypes
            import ctypes.wintypes as wintypes
        except Exception:
            return []

        class CREDENTIALW(ctypes.Structure):
            _fields_ = [
                ("Flags", wintypes.DWORD),
                ("Type", wintypes.DWORD),
                ("TargetName", wintypes.LPWSTR),
                ("Comment", wintypes.LPWSTR),
                ("LastWritten", wintypes.FILETIME),
                ("CredentialBlobSize", wintypes.DWORD),
                ("CredentialBlob", ctypes.POINTER(ctypes.c_byte)),
                ("Persist", wintypes.DWORD),
                ("AttributeCount", wintypes.DWORD),
                ("Attributes", ctypes.c_void_p),
                ("TargetAlias", wintypes.LPWSTR),
                ("UserName", wintypes.LPWSTR),
            ]

        pcredential = ctypes.POINTER(CREDENTIALW)
        ppcredential = ctypes.POINTER(pcredential)
        prefix = f"{self._service_prefix}:"
        profiles: set[str] = set()

        try:
            advapi32 = ctypes.WinDLL("Advapi32.dll")
            cred_enumerate = advapi32.CredEnumerateW
            cred_enumerate.argtypes = [
                wintypes.LPCWSTR,
                wintypes.DWORD,
                ctypes.POINTER(wintypes.DWORD),
                ctypes.POINTER(ppcredential),
            ]
            cred_enumerate.restype = wintypes.BOOL
            cred_free = advapi32.CredFree
            cred_free.argtypes = [ctypes.c_void_p]
            cred_free.restype = None

            count = wintypes.DWORD()
            creds = ppcredential()
            if not cred_enumerate(None, 0, ctypes.byref(count), ctypes.byref(creds)):
                return []
            try:
                cred_array = ctypes.cast(
                    creds, ctypes.POINTER(pcredential * count.value)
                ).contents
                for index in range(count.value):
                    target = cred_array[index].contents.TargetName or ""
                    service_name = ""
                    if target.startswith(prefix):
                        service_name = target
                    elif "@" in target:
                        _, possible_service = target.split("@", 1)
                        if possible_service.startswith(prefix):
                            service_name = possible_service
                    if not service_name:
                        continue
                    profile = service_name[len(prefix) :].strip()
                    if profile and profile != self._REGISTRY_SERVICE:
                        profiles.add(profile)
            finally:
                cred_free(creds)
        except Exception:
            return []

        return sorted(profiles)
