from datetime import date
from pathlib import Path

from odoo_task_porter.services.export_service import ExportService


def test_parse_deadline_accepts_date_string() -> None:
    assert ExportService._parse_deadline("2026-02-16") == date(2026, 2, 16)


def test_parse_deadline_accepts_odoo_datetime_string() -> None:
    assert ExportService._parse_deadline("2026-02-16 00:00:00") == date(2026, 2, 16)


class _Spec:
    version_name = "odoo_19"


class _RepoStub:
    def get_server_major_version(self) -> int | None:
        return 19

    def get_version_spec(self):
        return _Spec()

    def get_project_id(self, project_name: str) -> int:
        return 1

    def resolve_task_fields(self) -> dict[str, str | None]:
        return {
            "id": "id",
            "name": "name",
            "description": "description",
            "project": "project_id",
            "tags": "tag_ids",
            "stage": "stage_id",
            "deadline": None,
            "import_key": None,
            "estimation_hours": None,
            "owner": None,
        }

    def find_tasks(self, domain: list, fields: list[str]) -> list[dict]:
        return [
            {
                "id": 10,
                "name": "Task A",
                "description": "Description A",
                "tag_ids": [],
                "stage_id": [1, "To Do"],
            },
            {
                "id": 11,
                "name": "Task B",
                "description": "Description B",
                "tag_ids": [],
                "stage_id": [1, "To Do"],
            },
        ]

    def read_project_tags(self, tag_ids: list[int]) -> list[str]:
        return []


def test_export_reports_progress(tmp_path: Path) -> None:
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)
    (templates_dir / "dev.md").write_text(
        "\n".join(
            [
                "# {{TITLE}}",
                "",
                "## Metadonnees",
                "- Type: {{TYPE}}",
                "- Statut: {{STATUT}}",
                "- Priorite: {{PRIORITE}}",
                "- MoSCoW: {{MOSCOW}}",
                "- Estimation: {{ESTIMATION}}",
                "- Owner: {{OWNER}}",
                "- Deadline: {{DEADLINE}}",
                "- Liens: {{LIENS}}",
                "",
                "## Description",
                "{{DESCRIPTION}}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "out"

    calls: list[tuple[int, int]] = []
    report = ExportService(_RepoStub()).run(
        out_dir,
        "Projet",
        templates_dir,
        on_progress=lambda done, total: calls.append((done, total)),
    )

    assert len(report.items) == 2
    assert calls[0] == (0, 2)
    assert calls[-1] == (2, 2)
