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
    assert "<ul class=\"o_checklist\">" in html
    assert "<li>Item a faire</li>" in html
    assert "<li class=\"o_checked\">Item termine</li>" in html
    assert "<ol>" in html
    assert "<table" in html
    assert "<th>Col A</th>" in html
    assert "<td>A1</td>" in html


def test_markdown_to_odoo_html_supports_extended_checkboxes_and_table_separator() -> None:
    markdown = """## Checklist

+ [ ] Item plus
- [✓] Item coche
- ☑ Item unicode coche
- ☐ Item unicode vide

| Col A | Col B |
| --- | ——— |
| A1 | B1 |
"""
    html = markdown_to_odoo_html(markdown)

    assert "<ul class=\"o_checklist\">" in html
    assert "<li>Item plus</li>" in html
    assert "<li class=\"o_checked\">Item coche</li>" in html
    assert "<li class=\"o_checked\">Item unicode coche</li>" in html
    assert "<li>Item unicode vide</li>" in html
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


def test_parse_markdown_supports_front_matter_and_markdown_metadata(tmp_path: Path) -> None:
    content = """---
id: D-101
title: "Initialiser repo Django/DRF"
---

# D-101 - Initialiser repo Django/DRF

## Metadonnees
- **Type**: `dev`
- **Statut**: `todo`
- **Priorite**: `P1`
- **MoSCoW**: `Must`
- **Estimation**: `S`
- **Owner**: `@alice`

## Objectif
Texte.
"""
    path = tmp_path / "frontmatter.md"
    path.write_text(content, encoding="utf-8")

    parsed = parse_markdown(path)

    assert parsed.title == "D-101 - Initialiser repo Django/DRF"
    assert parsed.metadata.task_type == "dev"
    assert parsed.metadata.status == "todo"
    assert parsed.metadata.priority == "P1"
    assert parsed.metadata.moscow == "Must"
    assert parsed.metadata.estimation == "S"
    assert parsed.metadata.owner == "@alice"


def test_parse_markdown_extracts_task_code_from_metadata_id(tmp_path: Path) -> None:
    content = """# D-102 - Docker Compose

## Metadonnees
- ID: D-102
- Type: dev
- Statut: todo
- Priorite: P1
- MoSCoW: Must
- Estimation: S
- Owner: @alice
"""
    path = tmp_path / "task_code.md"
    path.write_text(content, encoding="utf-8")

    parsed = parse_markdown(path)

    assert parsed.task_code == "D-102"


def test_parse_markdown_extracts_dotted_task_code_from_title(tmp_path: Path) -> None:
    content = """# M-01.1 — API Projects CRUD

## Metadonnees
- Type: dev
- Statut: todo
- Priorite: P1
- MoSCoW: Must
- Estimation: S
- Owner: @alice
"""
    path = tmp_path / "task_code_dotted.md"
    path.write_text(content, encoding="utf-8")

    parsed = parse_markdown(path)

    assert parsed.task_code == "M-01.1"


def test_parse_markdown_accepts_custom_odoo_stage_name(tmp_path: Path) -> None:
    content = """# M-01.2 - API Spaces CRUD

## Metadonnees
- Type: dev
- Statut: spécification
- Priorite: P1
- MoSCoW: Must
- Estimation: S
- Owner: @alice
"""
    path = tmp_path / "custom_stage.md"
    path.write_text(content, encoding="utf-8")

    parsed = parse_markdown(path)

    assert parsed.metadata.status == "spécification"

def test_parse_markdown_accepts_aide_task_type(tmp_path: Path) -> None:
    content = """# AIDE-ERROR-001 - Error management

## Metadonnees
- Type: aide
- Statut: todo
- Priorite: P1
- MoSCoW: Must
- Estimation: S
"""
    path = tmp_path / "aide_task.md"
    path.write_text(content, encoding="utf-8")

    parsed = parse_markdown(path)

    assert parsed.metadata.task_type == "aide"


def test_parse_markdown_normalizes_moscow_with_annotation(tmp_path: Path) -> None:
    content = """# M-02.5 - Parsing contenu

## Metadonnees
- Type: dev
- Statut: todo
- Priorite: P1
- MoSCoW: Must *(a challenger)*
- Estimation: S
"""
    path = tmp_path / "moscow_annotation.md"
    path.write_text(content, encoding="utf-8")

    parsed = parse_markdown(path)

    assert parsed.metadata.moscow == "Must"
