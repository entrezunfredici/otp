"""Identifier helpers."""
from __future__ import annotations

import hashlib
import re
import unicodedata


TASK_CODE_PATTERN = r"[A-Za-z]+-\d+(?:\.\d+)*"
TASK_CODE_RE = re.compile(rf"\b({TASK_CODE_PATTERN})\b")


def extract_task_code(*values: str | None) -> str | None:
    """Extract a normalized task code from one or more strings."""
    for value in values:
        if not value:
            continue
        match = TASK_CODE_RE.search(value)
        if match:
            return match.group(1).upper()
    return None


def has_task_code(value: str, task_code: str) -> bool:
    """Return True when ``value`` contains ``task_code`` as a standalone token."""
    normalized_value = value.upper()
    normalized_code = task_code.strip().upper()
    if not normalized_value or not normalized_code:
        return False
    pattern = re.compile(rf"(?<![A-Z0-9.]){re.escape(normalized_code)}(?![A-Z0-9.])")
    return pattern.search(normalized_value) is not None


def normalize_task_identity(value: str, task_code: str | None = None) -> str:
    """Normalize a task title for resilient matching."""
    normalized = unicodedata.normalize("NFKD", value or "")
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    code = task_code or extract_task_code(normalized)
    if code:
        normalized = re.sub(
            rf"(?<![A-Za-z0-9]){re.escape(code)}(?![A-Za-z0-9])",
            " ",
            normalized,
            flags=re.I,
        )
    normalized = normalized.lower()
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def build_import_key(project: str, title: str, task_code: str | None = None) -> str:
    """Compute a stable hash for project and task identity."""
    stable_identity = (task_code or title).strip()
    payload = f"{project}::{stable_identity}".encode("utf-8")
    return hashlib.sha1(payload).hexdigest()[:12]
