"""Configuration command."""
from __future__ import annotations

import argparse
from pathlib import Path

from odoo_task_porter.cli.base_command import BaseCommand, CommandHelper
from odoo_task_porter.config.settings import (
    DEFAULT_CONFIG_PATH,
    init_config,
    load_config,
    upsert_paths,
)


class ConfigCommand(BaseCommand):
    name = "config"
    summary = "Initialiser ou gerer les chemins de configuration."

    def configure(self, parser: argparse.ArgumentParser) -> None:
        config_sub = parser.add_subparsers(dest="config_cmd", required=True)
        init_parser = config_sub.add_parser("init", help="Creer un fichier de configuration.")
        init_parser.add_argument("--path", type=Path, default=DEFAULT_CONFIG_PATH)
        paths_parser = config_sub.add_parser(
            "paths",
            help="Gerer les chemins de travail.",
        )
        paths_sub = paths_parser.add_subparsers(dest="paths_cmd", required=True)
        set_parser = paths_sub.add_parser(
            "set",
            help="Mettre a jour les chemins de la configuration.",
        )
        set_parser.add_argument("--templates-empty-dir", type=Path)
        set_parser.add_argument("--tasks-md-dir", type=Path)
        set_parser.add_argument("--export-out-dir", type=Path)
        paths_sub.add_parser("show", help="Afficher les chemins configures.")

    def execute(self, args: argparse.Namespace) -> int:
        if args.config_cmd == "init":
            path = init_config(args.path)
            print(f"Config initialized at {path}")
            return 0

        if args.config_cmd == "paths" and args.paths_cmd == "set":
            if (
                args.templates_empty_dir is None
                and args.tasks_md_dir is None
                and args.export_out_dir is None
            ):
                raise ValueError(
                    "Aucun chemin fourni. Utilise au moins une option parmi "
                    "--templates-empty-dir, --tasks-md-dir, --export-out-dir."
                )
            path = upsert_paths(
                templates_empty_dir=args.templates_empty_dir,
                tasks_md_dir=args.tasks_md_dir,
                export_out_dir=args.export_out_dir,
                path=args.config,
            )
            print(f"Paths updated in {path}")
            return 0

        if args.config_cmd == "paths" and args.paths_cmd == "show":
            config = load_config(args.config)
            print(f"templates_empty_dir={config.templates_empty_dir}")
            print(f"tasks_md_dir={config.tasks_md_dir}")
            print(f"export_out_dir={config.export_out_dir}")
            return 0

        return 1

    def helper(self) -> CommandHelper:
        return CommandHelper(
            name=self.name,
            summary=self.summary,
            usage=(
                "odoo-task-porter config init [--path <config.toml>] | "
                "odoo-task-porter config paths set [--templates-empty-dir <dir>] "
                "[--tasks-md-dir <dir>] [--export-out-dir <dir>] | "
                "odoo-task-porter config paths show"
            ),
        )
