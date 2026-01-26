"""Command-line interface for odoo-task-porter."""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
import sys

from odoo_task_porter.adapters.odoo_repo import OdooRepository
from odoo_task_porter.adapters.odoo_xmlrpc import OdooClient
from odoo_task_porter.config.auth import AuthManager
from odoo_task_porter.config.settings import DEFAULT_CONFIG_PATH, load_config, init_config
from odoo_task_porter.domain.errors import OdooError
from odoo_task_porter.services.export_service import ExportOptions, ExportService
from odoo_task_porter.services.import_service import ImportOptions, ImportService
from odoo_task_porter.services.lint_service import LintService


def main() -> int:
    parser = argparse.ArgumentParser(prog="odoo-task-porter")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--log-level", default="INFO")
    subparsers = parser.add_subparsers(dest="command", required=True)

    config_parser = subparsers.add_parser("config")
    config_sub = config_parser.add_subparsers(dest="config_cmd", required=True)
    init_parser = config_sub.add_parser("init")
    init_parser.add_argument("--path", type=Path, default=DEFAULT_CONFIG_PATH)

    auth_parser = subparsers.add_parser("auth")
    auth_sub = auth_parser.add_subparsers(dest="auth_cmd", required=True)
    auth_set = auth_sub.add_parser("set")
    auth_set.add_argument("--profile", required=True)
    auth_test = auth_sub.add_parser("test")
    auth_test.add_argument("--profile", required=True)
    auth_unset = auth_sub.add_parser("unset")
    auth_unset.add_argument("--profile", required=True)

    import_parser = subparsers.add_parser("import")
    import_parser.add_argument("--profile", required=True)
    import_parser.add_argument("--project", required=True)
    import_parser.add_argument("--tasks-md-dir", type=Path)
    import_parser.add_argument("--dry-run", action="store_true")
    import_parser.add_argument("--create-only", action="store_true")
    import_parser.add_argument("--report-json", type=Path)

    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("--profile", required=True)
    export_parser.add_argument("--project", required=True)
    export_parser.add_argument("--templates-empty-dir", type=Path)
    export_parser.add_argument("--export-out-dir", type=Path)
    export_parser.add_argument("--stage")
    export_parser.add_argument("--tag")
    export_parser.add_argument("--domain")
    export_parser.add_argument("--report-json", type=Path)

    lint_parser = subparsers.add_parser("lint")
    lint_parser.add_argument("--tasks-md-dir", type=Path)
    lint_parser.add_argument("--report-json", type=Path)

    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    if args.command == "config" and args.config_cmd == "init":
        path = init_config(args.path)
        print(f"Config initialized at {path}")
        return 0

    if args.command == "auth":
        return _handle_auth(args)

    if args.command == "lint":
        config = load_config(args.config)
        tasks_dir = args.tasks_md_dir or config.tasks_md_dir
        report = LintService().run(tasks_dir)
        _emit_report(report, args.report_json)
        return 0

    config = load_config(args.config)
    profile = config.profiles.get(args.profile)
    if not profile:
        raise OdooError(f"Profile '{args.profile}' not found in config.")
    auth_manager = AuthManager()
    auth = auth_manager.get(args.profile, profile.username)
    client = OdooClient(profile.url, profile.db, profile.username, auth.password)
    repo = OdooRepository(client)

    if args.command == "import":
        tasks_dir = args.tasks_md_dir or config.tasks_md_dir
        options = ImportOptions(dry_run=args.dry_run, create_only=args.create_only)
        report = ImportService(repo).run(tasks_dir, args.project, options)
        _emit_report(report, args.report_json)
        return 0

    if args.command == "export":
        export_dir = args.export_out_dir or config.export_out_dir
        templates_dir = args.templates_empty_dir or config.templates_empty_dir
        options = ExportOptions(stage=args.stage, tag=args.tag, domain=args.domain)
        report = ExportService(repo).run(export_dir, args.project, templates_dir, options)
        _emit_report(report, args.report_json)
        return 0

    return 1


def _handle_auth(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    profile = config.profiles.get(args.profile)
    if not profile:
        raise OdooError(f"Profile '{args.profile}' not found in config.")
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


def _emit_report(report, report_path: Path | None) -> None:
    payload = report.to_dict()
    if report_path:
        report_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Report written to {report_path}")
    else:
        print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())
