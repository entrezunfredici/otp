"""Path configuration helpers."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PathsConfig:
    """Stores configurable filesystem paths."""

    templates_empty_dir: Path
    tasks_md_dir: Path
    export_out_dir: Path

    def ensure_dirs(self) -> None:
        self.templates_empty_dir.mkdir(parents=True, exist_ok=True)
        self.tasks_md_dir.mkdir(parents=True, exist_ok=True)
        self.export_out_dir.mkdir(parents=True, exist_ok=True)
