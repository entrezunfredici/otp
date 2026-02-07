"""CLI report output helpers."""
from __future__ import annotations

import json
from pathlib import Path


def emit_report(report, report_path: Path | None) -> None:
    """Print a report or write it to JSON."""
    payload = report.to_dict()
    if report_path:
        report_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Report written to {report_path}")
    else:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
