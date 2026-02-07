"""Authentication command."""
from __future__ import annotations

import argparse

from odoo_task_porter.cli.base_command import BaseCommand, CommandHelper
from odoo_task_porter.cli.generic_functions import load_app_config, require_profile


class AuthCommand(BaseCommand):
    name = "auth"
    summary = "Gérer les identifiants dans keyring."

    def configure(self, parser: argparse.ArgumentParser) -> None:
        auth_sub = parser.add_subparsers(dest="auth_cmd", required=True)

        auth_set = auth_sub.add_parser("set", help="Stocker le mot de passe.")
        auth_set.add_argument("--profile", required=True)

        auth_test = auth_sub.add_parser("test", help="Tester l'accès au mot de passe.")
        auth_test.add_argument("--profile", required=True)

        auth_unset = auth_sub.add_parser("unset", help="Supprimer le mot de passe.")
        auth_unset.add_argument("--profile", required=True)

    def execute(self, args: argparse.Namespace) -> int:
        from odoo_task_porter.config.auth import AuthManager

        config = load_app_config(args.config)
        profile = require_profile(config, args.profile)
        manager = AuthManager()

        if args.auth_cmd == "set":
            manager.set(args.profile, profile.username)
            print("Credentials stored in keyring.")
            return 0
        if args.auth_cmd == "test":
            result = manager.test(args.profile, profile.username)
            print(f"Credentials available via {result.source}.")
            return 0
        if args.auth_cmd == "unset":
            manager.unset(args.profile, profile.username)
            print("Credentials removed from keyring.")
            return 0
        return 1

    def helper(self) -> CommandHelper:
        return CommandHelper(
            name=self.name,
            summary=self.summary,
            usage="odoo-task-porter auth {set|test|unset} --profile <name>",
        )
