"""Configuration command."""
from __future__ import annotations

import argparse
from pathlib import Path

from odoo_task_porter.cli.base_command import BaseCommand, CommandHelper
from odoo_task_porter.cli.inquirer_helper import can_prompt_interactively, prompt_text
from odoo_task_porter.config.settings import (
    DEFAULT_CONFIG_PATH,
    init_config,
    list_profile_names,
    upsert_profile,
)


class ConfigCommand(BaseCommand):
    name = "config"
    summary = "Initialiser ou gerer la configuration."

    def configure(self, parser: argparse.ArgumentParser) -> None:
        config_sub = parser.add_subparsers(dest="config_cmd", required=True)
        init_parser = config_sub.add_parser("init", help="Creer un fichier de configuration.")
        init_parser.add_argument("--path", type=Path, default=DEFAULT_CONFIG_PATH)
        profile_parser = config_sub.add_parser(
            "profile",
            help="Gerer les profils utilisateurs.",
        )
        profile_sub = profile_parser.add_subparsers(dest="profile_cmd", required=True)
        set_parser = profile_sub.add_parser(
            "set",
            help="Creer ou mettre a jour un profil.",
        )
        set_parser.add_argument("--name")
        set_parser.add_argument("--url")
        set_parser.add_argument("--db")
        set_parser.add_argument("--username")
        set_parser.add_argument(
            "--interactive",
            action="store_true",
            help="Demande les champs manquants en mode interactif.",
        )
        profile_sub.add_parser(
            "list",
            help="Lister les profils configures.",
        )

    def execute(self, args: argparse.Namespace) -> int:
        if args.config_cmd != "init":
            if args.config_cmd == "profile" and args.profile_cmd == "set":
                name, url, db, username = self._resolve_profile_input(args)
                path = upsert_profile(
                    profile_name=name,
                    url=url,
                    db=db,
                    username=username,
                    path=args.config,
                )
                print(f"Profile '{name}' saved in {path}")
                return 0
            if args.config_cmd == "profile" and args.profile_cmd == "list":
                profiles = list_profile_names(args.config)
                if not profiles:
                    print("No profiles configured.")
                    return 0
                for profile in profiles:
                    print(profile)
                return 0
            return 1
        path = init_config(args.path)
        print(f"Config initialized at {path}")
        return 0

    def helper(self) -> CommandHelper:
        return CommandHelper(
            name=self.name,
            summary=self.summary,
            usage=(
                "odoo-task-porter config init [--path <config.toml>] | "
                "odoo-task-porter config profile set [--name <name>] [--url <url>] "
                "[--db <db>] [--username <user>] [--interactive] | "
                "odoo-task-porter config profile list"
            ),
        )

    def _resolve_profile_input(
        self, args: argparse.Namespace
    ) -> tuple[str, str, str, str]:
        values = {
            "name": args.name,
            "url": args.url,
            "db": args.db,
            "username": args.username,
        }
        missing = [key for key, value in values.items() if not value]
        if not missing:
            return values["name"], values["url"], values["db"], values["username"]

        if args.interactive or can_prompt_interactively():
            try:
                if not values["name"]:
                    values["name"] = prompt_text("Nom du profil (ex: dev):")
                if not values["url"]:
                    values["url"] = prompt_text("URL Odoo (ex: https://odoo.example.com):")
                if not values["db"]:
                    values["db"] = prompt_text("Base de donnees (ex: odoo):")
                if not values["username"]:
                    values["username"] = prompt_text("Nom utilisateur (email):")
            except ModuleNotFoundError as exc:
                raise RuntimeError(
                    "InquirerPy n'est pas installe. Lance 'pip install -e .' puis reessaie."
                ) from exc

            still_missing = [key for key, value in values.items() if not value]
            if still_missing:
                missing_text = ", ".join(still_missing)
                raise ValueError(f"Champs manquants apres saisie interactive: {missing_text}")
            return values["name"], values["url"], values["db"], values["username"]

        missing_text = ", ".join(missing)
        raise ValueError(
            f"Champs manquants: {missing_text}. Passe les options ou utilise --interactive."
        )
