from datetime import date

from odoo_task_porter.services.export_service import ExportService


def test_parse_deadline_accepts_date_string() -> None:
    assert ExportService._parse_deadline("2026-02-16") == date(2026, 2, 16)


def test_parse_deadline_accepts_odoo_datetime_string() -> None:
    assert ExportService._parse_deadline("2026-02-16 00:00:00") == date(2026, 2, 16)
