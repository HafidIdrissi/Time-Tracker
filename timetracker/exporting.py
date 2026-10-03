"""Local CSV and JSON exports of stored activity periods."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from .database import ActivityDatabase
from .models import ActivityPeriod

EXPORT_FIELDS = (
    "application",
    "window_title",
    "started_at",
    "ended_at",
    "duration_seconds",
    "is_idle",
)


def period_row(period: ActivityPeriod) -> dict[str, object]:
    """Return the documented export fields for one stored period."""

    return {
        "application": period.application,
        "window_title": period.window_title,
        "started_at": period.started_at.isoformat(),
        "ended_at": period.ended_at.isoformat(),
        "duration_seconds": period.duration_seconds,
        "is_idle": period.is_idle,
    }


def export_activity(database_path: str | Path, destination: str | Path, file_format: str) -> Path:
    """Write every stored period to ``destination`` without modifying the database."""

    normalized = file_format.casefold()
    if normalized not in {"csv", "json"}:
        raise ValueError("file_format must be 'csv' or 'json'")

    destination_path = Path(destination)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    partial_path = destination_path.with_name(destination_path.name + ".partial")

    source_path = Path(database_path)
    try:
        if source_path.is_file():
            with ActivityDatabase(source_path) as database:
                rows = [period_row(period) for period in database.all_periods()]
        else:
            rows = []
        if normalized == "csv":
            with partial_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=EXPORT_FIELDS, quoting=csv.QUOTE_MINIMAL)
                writer.writeheader()
                writer.writerows(rows)
        else:
            partial_path.write_text(
                json.dumps(rows, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        partial_path.replace(destination_path)
    except BaseException:
        partial_path.unlink(missing_ok=True)
        raise
    return destination_path
