"""Authentication command."""
from __future__ import annotations

import argparse

from odoo_task_porter.cli.base_command import BaseCommand, CommandHelper
from odoo_task_porter.cli.inquirer_helper import (
    can_prompt_interactively,
    prompt_checkbox,
    prompt_secret,
    prompt_text,
)


class AuthCommand(BaseCommand):
    name = "auth"
    summary = "Gerer les identifiants dans keyring."

    def configure(self, parser: argparse.ArgumentParser) -> None:
        auth_sub = parser.add_subparsers(dest="auth_cmd", required=True)

        auth_set = auth_sub.add_parser("set", help="Stocker les identifiants.")
        auth_set.add_argument("--profile")
        auth_set.add_argument("--username")
        auth_set.add_argument("--url")
        auth_set.add_argument("--db")
        auth_set.add_argument(
            "--interactive",
            action="store_true",
            help="Demander les champs manquants via inquirer.",
        )

        auth_test = auth_sub.add_parser("test", help="Tester l'acces aux identifiants.")
        auth_test.add_argument("--profile", required=True)

        auth_unset = auth_sub.add_parser("unset", help="Supprimer les identifiants.")
        auth_unset.add_argument("--profile")
        auth_unset.add_argument(
            "--interactive",
            action="store_true",
            help="Selectionner un ou plusieurs profils a supprimer via inquirer.",
        )

    def execute(self, args: argparse.Namespace) -> int:
        from odoo_task_porter.config.auth import AuthManager

        manager = AuthManager()

        if args.auth_cmd == "set":
            profile = self._resolve_profile(args, action_name="set")
            values = self._resolve_set_values(args)
            manager.set(
                profile,
                username=values["username"],
                url=values["url"],
                db=values["db"],
                password=values["password"],
            )
            print("Credentials (url/db/username/password) stored in keyring.")
            return 0
        if args.auth_cmd == "test":
            result = manager.test(args.profile)
            print(
                "Credentials available via "
                f"{result.source}: url={result.url}, db={result.db}, username={result.username}."
            )
            return 0
        if args.auth_cmd == "unset":
            profiles = self._resolve_unset_profiles(args, manager)
            for profile in profiles:
                manager.unset(profile)
            print(f"Credentials removed for {len(profiles)} profile(s).")
            return 0
        return 1

    def helper(self) -> CommandHelper:
        return CommandHelper(
            name=self.name,
            summary=self.summary,
            usage=(
                "odoo-task-porter auth set [--profile <name>] [--username <user>] "
                "[--url <url>] [--db <db>] [--interactive] | "
                "odoo-task-porter auth test --profile <name> | "
                "odoo-task-porter auth unset [--profile <name>] [--interactive]"
            ),
        )

    def _resolve_profile(self, args: argparse.Namespace, action_name: str) -> str:
        profile = (args.profile or "").strip()
        if profile:
            return profile
        if action_name != "set":
            raise ValueError("L'option --profile est obligatoire.")
        if not (args.interactive or can_prompt_interactively()):
            raise ValueError("Champs manquants: profile. Passe --profile ou utilise --interactive.")
        try:
            profile = prompt_text("Nom du profil (ex: dev):")
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "InquirerPy n'est pas installe. Lance 'pip install -e .' puis reessaie."
            ) from exc
        except KeyboardInterrupt as exc:
            raise RuntimeError("Saisie annulee par l'utilisateur.") from exc
        profile = profile.strip()
        if not profile:
            raise ValueError("Le profile ne peut pas etre vide.")
        return profile

    def _resolve_set_values(self, args: argparse.Namespace) -> dict[str, str]:
        values: dict[str, str] = {
            "username": (args.username or "").strip(),
            "url": (args.url or "").strip(),
            "db": (args.db or "").strip(),
            "password": "",
        }
        missing = [key for key, value in values.items() if not value]
        if not missing:
            return values

        if not (args.interactive or can_prompt_interactively()):
            missing_text = ", ".join(missing)
            raise ValueError(
                f"Champs manquants: {missing_text}. Passe les options ou utilise --interactive."
            )

        while True:
            missing = [key for key, value in values.items() if not value]
            if not missing:
                return values
            field = missing[0]
            try:
                if field == "username":
                    values[field] = prompt_text("Odoo username (email):")
                elif field == "url":
                    values[field] = prompt_text("Odoo URL:")
                elif field == "db":
                    values[field] = prompt_text("Odoo database:")
                else:
                    values[field] = prompt_secret("Odoo password:")
            except ModuleNotFoundError as exc:
                raise RuntimeError(
                    "InquirerPy n'est pas installe. Lance 'pip install -e .' puis reessaie."
                ) from exc
            except KeyboardInterrupt as exc:
                raise RuntimeError("Saisie annulee par l'utilisateur.") from exc
            values[field] = values[field].strip()

    def _resolve_unset_profiles(self, args: argparse.Namespace, manager) -> list[str]:
        direct_profile = (args.profile or "").strip()
        if direct_profile:
            return [direct_profile]

        if not (args.interactive or can_prompt_interactively()):
            raise ValueError("Passe --profile ou utilise --interactive pour choisir les profils.")

        profiles = manager.list_profiles()
        if not profiles:
            raise ValueError(
                "Aucun profil connu pour suppression. Utilise --profile si le profil existe deja en keyring."
            )

        try:
            selected = prompt_checkbox(
                "Selectionne les profils a supprimer (Espace pour cocher):",
                profiles,
            )
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "InquirerPy n'est pas installe. Lance 'pip install -e .' puis reessaie."
            ) from exc
        except KeyboardInterrupt as exc:
            raise RuntimeError("Saisie annulee par l'utilisateur.") from exc

        if not selected:
            raise ValueError("Aucun profil selectionne.")
        return selected
