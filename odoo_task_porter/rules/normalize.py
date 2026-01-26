"""Normalization helpers."""
from __future__ import annotations

import re
import unicodedata


def slugify(value: str) -> str:
    """Return a URL-friendly slug."""
    normalized = unicodedata.normalize("NFKD", value)
    cleaned = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", cleaned).strip("-")
    return cleaned.lower() or "task"
