from pathlib import Path

from odoo_task_porter.adapters.markdown import markdown_to_odoo_html, parse_markdown


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


def test_markdown_to_odoo_html_supports_core_blocks() -> None:
    markdown = """## Titre

- [ ] Item a faire
- [x] Item termine
- Liste simple

| Col A | Col B |
| --- | --- |
| A1 | B1 |

1. Etape 1
2. Etape 2
"""
    html = markdown_to_odoo_html(markdown)
    assert "<h2>Titre</h2>" in html
    assert "<input type=\"checkbox\" disabled>" in html
    assert "<input type=\"checkbox\" disabled checked>" in html
    assert "<ul>" in html
    assert "<ol>" in html
    assert "<table" in html
    assert "<th>Col A</th>" in html
    assert "<td>A1</td>" in html


def test_parse_markdown_ignores_indented_list_items_in_metadata_section(tmp_path: Path) -> None:
    content = """# Test

## Métadonnées
- Type: produit
- Statut: todo
- Priorité: P1
- MoSCoW: Must
- Estimation: M
- Liens:
  - Sous-item: ne doit pas ecraser MoSCoW

## Description
Ok
"""
    path = tmp_path / "indented.md"
    path.write_text(content, encoding="utf-8")
    parsed = parse_markdown(path)
    assert parsed.metadata.moscow == "Must"
