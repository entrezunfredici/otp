# odoo_task_porter

Prototype v1 pour importer et exporter des taches Odoo 19 via XML-RPC et des fichiers Markdown.

## Gestion d'un environnement virtuel

Creation de l'environnement virtuel

```bash
python -m venv /otpenv
```

Activation de l'environnement virtuel

```bash
\otpenv\Scripts\Activate.ps1
```

## Installation

Installation du script

```bash
pip install -e .
```

## Configuration

Initialiser un fichier de configuration (sans secrets) :

```bash
odoo-task-porter config init
```

Mettre a jour les chemins de travail :

```bash
odoo-task-porter config paths set --templates-empty-dir templates/empty --tasks-md-dir tasks_md --export-out-dir exported
```

Afficher les chemins configures :

```bash
odoo-task-porter config paths show
```

Le fichier genere (par defaut `~/.config/odoo-task-porter/config.toml`) contient :

```toml
[paths]
templates_empty_dir = "templates/empty"
tasks_md_dir = "tasks_md"
export_out_dir = "exported"
```

## Authentification

Stocker un profil de connexion complet dans keyring :

```bash
odoo-task-porter auth set --profile dev --url https://odoo.example.com --db odoo --username user@example.com
```

Mode interactif (inquirer) pour completer les champs manquants :

```bash
odoo-task-porter auth set --profile dev --interactive
```

Tester l'acces aux identifiants :

```bash
odoo-task-porter auth test --profile dev
```

Supprimer les identifiants :

```bash
odoo-task-porter auth unset --profile dev
```

Supprimer plusieurs profils via une liste a choix multiple :

```bash
odoo-task-porter auth unset --interactive
```

Fallbacks : si le mot de passe n'est pas en keyring, la variable `ODOO_PASSWORD` peut etre utilisee. En mode TTY, les champs manquants peuvent etre saisis au prompt.

## Import

```bash
odoo-task-porter import --profile dev --project "Mon projet" --tasks-md-dir tasks_md
```

Options :

- `--dry-run` : pas d'ecriture Odoo.
- `--create-only` : n'exige pas `x_import_key` (mode creation uniquement).
- `--report-json path.json` : ecrire le rapport en JSON.

Par defaut, le champ custom `x_import_key` doit exister sur `project.task`.

## Export

```bash
odoo-task-porter export --profile dev --project "Mon projet" \
  --templates-empty-dir templates/empty --export-out-dir exported
```

Filtres :

- `--stage "In Progress"`
- `--tag "type_dev"`
- `--domain "[['user_id','!=',False]]"`

Compatibilite versions Odoo :

- La version serveur est detectee a la connexion (v18/v19).
- Le script charge un mapping Python versionne dans `odoo_task_porter/versions/`.
- Le mapping v18 est dans `odoo_task_porter/versions/odoo_18.py`.
- Le mapping v19 est dans `odoo_task_porter/versions/odoo_19.py`.
- Ces fichiers definissent les correspondances de modeles et de champs.
- Le mapping `project.task` est maintenant declare de facon etendue (alias -> candidats de champs).
- Le mapping etendu couvre aussi les modeles `project.project`, `project.tags`, `project.task.type` et `res.users`.
- Les commandes `import` et `export` utilisent ce mapping + verification des champs disponibles.
- Si la version n'est pas detectee, un fallback automatique vers le mapping v19 est applique.

## Lint

Valider des fichiers markdown sans Odoo :

```bash
odoo-task-porter lint --tasks-md-dir tasks_md
```

## Exemples

- `examples/import_task_example.md`
- `examples/export_task_example.md`

