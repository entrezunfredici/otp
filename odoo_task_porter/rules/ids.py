"""Identifier helpers."""
from __future__ import annotations

import hashlib


def build_import_key(project: str, title: str) -> str:
    """Compute a stable hash for project and title."""
    payload = f"{project}::{title}".encode("utf-8")
    return hashlib.sha1(payload).hexdigest()[:12]
