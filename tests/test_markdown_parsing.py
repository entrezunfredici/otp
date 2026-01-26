from pathlib import Path

from odoo_task_porter.adapters.markdown import parse_markdown


def test_parse_markdown_metadata(tmp_path: Path) -> None:
    content = """# OAuth2 login — Dev (Auth)

## Métadonnées
- Type: dev
- Statut: todo
- Priorité: P1
- MoSCoW: Must
- Estimation: 2h
- Owner: @alice
- Deadline: 2025-01-20
- Liens: https://example.com

## Description
Texte de description.
"""
    path = tmp_path / "task.md"
    path.write_text(content, encoding="utf-8")

    parsed = parse_markdown(path)

    assert parsed.title == "OAuth2 login — Dev (Auth)"
    assert parsed.metadata.task_type == "dev"
    assert parsed.metadata.status == "todo"
    assert parsed.metadata.priority == "P1"
    assert parsed.metadata.moscow == "Must"
    assert parsed.metadata.estimation == "2h"
    assert parsed.metadata.owner == "@alice"
    assert parsed.metadata.deadline.isoformat() == "2025-01-20"
    assert parsed.metadata.links == ["https://example.com"]
