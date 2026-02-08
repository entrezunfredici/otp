"""Versioned mapping resolver for Odoo integrations."""
from __future__ import annotations

from odoo_task_porter.versions.odoo_18 import SPEC as V18_SPEC
from odoo_task_porter.versions.odoo_19 import SPEC as V19_SPEC
from odoo_task_porter.versions.spec import OdooVersionSpec


def resolve_version_spec(major_version: int | None) -> OdooVersionSpec:
    """Return mapping spec for detected Odoo major version."""
    if major_version == 18:
        return V18_SPEC
    if major_version == 19:
        return V19_SPEC
    return V19_SPEC


__all__ = ["OdooVersionSpec", "resolve_version_spec"]
