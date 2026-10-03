"""Consistent local snapshots of the activity database."""

from __future__ import annotations

import sqlite3
from pathlib import Path


def backup_activity_database(source: str | Path, destination: str | Path) -> Path:
    """Copy committed activity into ``destination`` without changing ``source``.

    The destination is replaced only after the SQLite backup succeeds. A failed
    attempt removes its temporary file.
    """

    source_path = Path(source)
    destination_path = Path(destination)
    if not source_path.is_file():
        raise FileNotFoundError(f"Activity database not found: {source_path}")
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    partial_path = destination_path.with_name(destination_path.name + ".partial")
    if partial_path.exists():
        partial_path.unlink()

    source_connection = sqlite3.connect(source_path)
    try:
        destination_connection = sqlite3.connect(partial_path)
        try:
            source_connection.backup(destination_connection)
        finally:
            destination_connection.close()
        partial_path.replace(destination_path)
    except BaseException:
        partial_path.unlink(missing_ok=True)
        raise
    finally:
        source_connection.close()
    return destination_path
