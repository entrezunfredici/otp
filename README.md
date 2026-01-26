# odoo_task_porter

Prototype v1 pour importer et exporter des tâches Odoo 19 via XML-RPC et des fichiers Markdown.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Configuration

Initialiser un fichier de configuration (sans secrets) :

```bash
odoo-task-porter config init
```

Le fichier généré (par défaut `~/.config/odoo-task-porter/config.toml`) contient :

```toml
[paths]
templates_empty_dir = "templates/empty"
tasks_md_dir = "tasks_md"
export_out_dir = "exported"

[profiles.dev]
url = "https://odoo.example.com"
db = "odoo"
username = "user@example.com"
```

## Authentification

Stocker le mot de passe dans keyring :

```bash
odoo-task-porter auth set --profile dev
```

Tester l'accès au mot de passe (keyring/env/prompt) :

```bash
odoo-task-porter auth test --profile dev
```

Supprimer les identifiants :

```bash
odoo-task-porter auth unset --profile dev
```

Fallbacks : si keyring est indisponible, la variable `ODOO_PASSWORD` est utilisée (avec warning), sinon un prompt est affiché si un TTY est disponible.

## Import

```bash
odoo-task-porter import --profile dev --project "Mon projet" --tasks-md-dir tasks_md
```

Options :
- `--dry-run` : pas d'écriture Odoo.
- `--create-only` : n'exige pas `x_import_key` (mode création uniquement).
- `--report-json path.json` : écrire le rapport en JSON.

⚠️ Par défaut, le champ custom `x_import_key` doit exister sur `project.task`.

## Export

```bash
odoo-task-porter export --profile dev --project "Mon projet" \
  --templates-empty-dir templates/empty --export-out-dir exported
```

Filtres :
- `--stage "In Progress"`
- `--tag "type_dev"`
- `--domain "[['user_id','!=',False]]"`

## Lint

Valider des fichiers markdown sans Odoo :

```bash
odoo-task-porter lint --tasks-md-dir tasks_md
```

## Exemples

- `examples/import_task_example.md`
- `examples/export_task_example.md`
