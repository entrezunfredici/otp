"""Configuration loading and saving."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import tomllib

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "odoo-task-porter" / "config.toml"


@dataclass(frozen=True)
class ProfileConfig:
    """Holds configuration for a single profile."""

    name: str
    url: str
    db: str
    username: str


@dataclass(frozen=True)
class AppConfig:
    """Application configuration loaded from disk."""

    profiles: dict[str, ProfileConfig]
    templates_empty_dir: Path
    tasks_md_dir: Path
    export_out_dir: Path


def load_config(path: Path | None = None) -> AppConfig:
    """Load configuration from TOML file."""
    config_path = path or DEFAULT_CONFIG_PATH
    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found at {config_path}. Run 'config init'."
        )
    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    paths = data.get("paths", {})
    profiles_data = data.get("profiles", {})
    profiles: dict[str, ProfileConfig] = {}
    for name, payload in profiles_data.items():
        profiles[name] = ProfileConfig(
            name=name,
            url=payload["url"],
            db=payload["db"],
            username=payload["username"],
        )
    return AppConfig(
        profiles=profiles,
        templates_empty_dir=Path(paths.get("templates_empty_dir", "templates/empty")),
        tasks_md_dir=Path(paths.get("tasks_md_dir", "tasks_md")),
        export_out_dir=Path(paths.get("export_out_dir", "exported")),
    )


def init_config(path: Path | None = None) -> Path:
    """Initialize an empty configuration file without secrets."""
    config_path = path or DEFAULT_CONFIG_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
    if config_path.exists():
        return config_path
    default_payload: dict[str, Any] = {
        "paths": {
            "templates_empty_dir": "templates/empty",
            "tasks_md_dir": "tasks_md",
            "export_out_dir": "exported",
        },
        "profiles": {
            "dev": {
                "url": "https://odoo.example.com",
                "db": "odoo",
                "username": "user@example.com",
            }
        },
    }
    content = _render_toml(default_payload)
    config_path.write_text(content, encoding="utf-8")
    return config_path


def _render_toml(payload: dict[str, Any]) -> str:
    """Render a minimal TOML string from nested dictionaries."""
    lines: list[str] = []
    for section, values in payload.items():
        if isinstance(values, dict) and all(isinstance(v, dict) for v in values.values()):
            lines.append(f"[{section}]")
            lines.append("")
            for key, sub_values in values.items():
                lines.append(f"[{section}.{key}]")
                for sub_key, sub_value in sub_values.items():
                    lines.append(f"{sub_key} = \"{sub_value}\"")
                lines.append("")
        elif isinstance(values, dict):
            lines.append(f"[{section}]")
            for key, value in values.items():
                lines.append(f"{key} = \"{value}\"")
            lines.append("")
    return "\n".join(lines).strip() + "\n"
