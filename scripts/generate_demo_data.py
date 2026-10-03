#!/usr/bin/env python
"""Write a deterministic fictional activity database for interface checks."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from timetracker.database import ActivityDatabase
from timetracker.models import ActivityState


def demo_rows() -> list[tuple[ActivityState, datetime, datetime]]:
    """Return the same fictional periods on every invocation."""

    day = datetime(2026, 9, 16, tzinfo=timezone.utc)
    rows: list[tuple[ActivityState, datetime, datetime]] = [
        (
            ActivityState("Code.exe", "Demo project — fictional"),
            day.replace(hour=9),
            day.replace(hour=10, minute=15),
        ),
        (
            ActivityState("chrome.exe", "Fictional inbox gmail - Google Chrome"),
            day.replace(hour=10, minute=15),
            day.replace(hour=10, minute=45),
        ),
        (
            ActivityState("Idle", "No keyboard or mouse activity", is_idle=True),
            day.replace(hour=10, minute=45),
            day.replace(hour=11),
        ),
        (
            ActivityState("steam.exe", "Fictional game library"),
            day.replace(hour=18),
            day.replace(hour=18, minute=40),
        ),
        (
            ActivityState("chrome.exe", "Fictional youtube evening - Google Chrome"),
            day.replace(hour=23, minute=40),
            day + timedelta(days=1, minutes=20),
        ),
    ]
    return rows


def generate_demo_database(output_directory: str | Path) -> Path:
    """Create ``activity.db`` in a new or empty output directory.

    Refuses to replace an existing database and never chooses the installed
    application data directory.
    """

    destination_dir = Path(output_directory)
    database_path = destination_dir / "activity.db"
    if database_path.exists() or Path(str(database_path) + "-wal").exists():
        raise FileExistsError(f"Refusing to overwrite {database_path}")
    destination_dir.mkdir(parents=True, exist_ok=True)
    with ActivityDatabase(database_path) as database:
        for state, started_at, ended_at in demo_rows():
            period_id = database.create_period(state, started_at)
            database.update_period(period_id, started_at, ended_at)
    return database_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a fictional activity database in an explicit directory."
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="New directory that will contain activity.db",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        path = generate_demo_database(args.output)
    except FileExistsError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
