"""Local CSV and JSON exports of stored activity periods."""

from __future__ import annotations

import csv
import json
import math
import os
import tempfile
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


def _same_file(left: Path, right: Path) -> bool:
    if left.resolve() == right.resolve():
        return True
    try:
        return left.exists() and right.exists() and left.samefile(right)
    except OSError:
        return False


def export_activity(database_path: str | Path, destination: str | Path, file_format: str) -> Path:
    """Write every stored period to ``destination`` without modifying the database."""

    normalized = file_format.casefold()
    if normalized not in {"csv", "json"}:
        raise ValueError("file_format must be 'csv' or 'json'")

    source_path = Path(database_path)
    destination_path = Path(destination)
    if _same_file(source_path, destination_path):
        raise ValueError("The export destination must be a different file from the activity database")

    if source_path.is_file():
        with ActivityDatabase(source_path) as database:
            rows = [period_row(period) for period in database.all_periods()]
    else:
        rows = []

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination_path.name}.",
        suffix=".tmp",
        dir=destination_path.parent,
    )
    os.close(descriptor)
    temporary_path = Path(temporary_name)
    try:
        if normalized == "csv":
            with temporary_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=EXPORT_FIELDS, quoting=csv.QUOTE_MINIMAL)
                writer.writeheader()
                writer.writerows(rows)
        else:
            for row_number, row in enumerate(rows, start=1):
                duration = row["duration_seconds"]
                if isinstance(duration, float) and not math.isfinite(duration):
                    raise ValueError(
                        "JSON export row "
                        f"{row_number} has a non-finite duration_seconds value"
                    )
            temporary_path.write_text(
                json.dumps(rows, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                encoding="utf-8",
            )
        temporary_path.replace(destination_path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise
    return destination_path
