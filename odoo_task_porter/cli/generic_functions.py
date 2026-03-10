"""Generic CLI composition helpers."""
from __future__ import annotations

import inquirer, sys
from rich.progress import Progress, BarColumn, DownloadColumn, TextColumn, TransferSpeedColumn, TimeRemainingColumn, SpinnerColumn, TaskProgressColumn
from pathlib import Path
from odoo_task_porter.adapters.odoo_repo import OdooRepository
from odoo_task_porter.adapters.odoo_client import OdooClient
from odoo_task_porter.config.settings import AppConfig, load_config


def load_app_config(config_path: Path) -> AppConfig:
    """Load application configuration from a CLI-provided path."""
    return load_config(config_path)


def build_repository(profile_name: str) -> OdooRepository:
    """Create an authenticated Odoo repository for a given auth profile."""
    from odoo_task_porter.config.auth import AuthManager

    auth = AuthManager().get(
        profile_name,
    )
    client = OdooClient(auth.url, auth.db, auth.username, auth.password)
    return OdooRepository(client)

def inquirer_question(field_name: str, metadata: dict[str], default_value: any=None, overwrite_message: str=None, inquirer_theme=None):
    questions = []
    match metadata['inquirer_type']:
        case "list":
            questions.append(inquirer.List(field_name, message=overwrite_message or f"Which of these {field_name} did you choose? ➞ ", choices=metadata["choices"], default=default_value))
        case "checkbox":
            questions.append(inquirer.Checkbox(field_name, message=overwrite_message or f"Which of these {field_name} did you choose? ➞ ", choices=metadata["choices"], default=default_value))
        case "text":
            questions.append(inquirer.Text(field_name, message=overwrite_message or f"What is your {field_name}? ➞ ", default=default_value))
        case "password":
            questions.append(inquirer.Password(field_name, message=overwrite_message or f"What is your {field_name}? ➞ ", default=default_value))
        case "confirm":
            questions.append(inquirer.Confirm(field_name, message=overwrite_message or f"Do you want {field_name}? ➞ ", default=default_value))
        case "path":
            questions.append(inquirer.Path(field_name, message=overwrite_message or f"Where is your {field_name}? ➞ ", default=default_value))
        case "editor":
            questions.append(inquirer.Editor(field_name, message=overwrite_message or f"What is your {field_name}? ➞ ", default=default_value))
        case _:
            print(f"the {field_name}'s {type} type doesn't exist in DataType's get_data() function")
            sys.exit(1)
    return inquirer.prompt(questions, theme=inquirer_theme)[field_name]

def with_progress_bar(tag: str, total: int, action):
    with Progress(
        TextColumn("   ║║"),
        SpinnerColumn(style="bold orange1"),
        TextColumn("{task.description}"),
        BarColumn(bar_width=50, complete_style="orange1", finished_style="bold green", pulse_style="dim"),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        TaskProgressColumn(),
    ) as progress:
        task_id = progress.add_task(tag, total=total)
        action(progress, task_id)
