import pytest

from odoo_task_porter.adapters.markdown import parse_markdown
from odoo_task_porter.domain.errors import ValidationError


def test_missing_metadata_fields(tmp_path):
    content = """# Missing fields

## Métadonnées
- Type: dev
- Statut: todo
"""
    path = tmp_path / "task.md"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(ValidationError):
        parse_markdown(path)
