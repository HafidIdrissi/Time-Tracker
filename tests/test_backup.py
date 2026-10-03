from __future__ import annotations

import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from timetracker.backup import backup_activity_database
from timetracker.database import ActivityDatabase
from timetracker.models import ActivityState


class BackupTests(unittest.TestCase):
    def test_open_connection_write_is_included_and_source_stays_unchanged(self) -> None:
        start = datetime(2026, 1, 15, 9, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "activity.db"
            destination = root / "nested" / "backup.db"
            with ActivityDatabase(source) as database:
                period_id = database.create_period(ActivityState("Code.exe", "Fictional"), start)
                database.update_period(period_id, start, start + timedelta(minutes=3))
                backup_activity_database(source, destination)
                original = database.periods_between(start - timedelta(days=1), start + timedelta(days=1))
            with ActivityDatabase(destination) as copy:
                copied = copy.periods_between(start - timedelta(days=1), start + timedelta(days=1))
            with ActivityDatabase(source) as database:
                after = database.periods_between(start - timedelta(days=1), start + timedelta(days=1))
        self.assertEqual(len(copied), 1)
        self.assertEqual(copied[0].window_title, "Fictional")
        self.assertEqual(copied[0].duration_seconds, 180)
        self.assertEqual(after[0].duration_seconds, original[0].duration_seconds)
        self.assertFalse(destination.with_name(destination.name + ".partial").exists())

    def test_failed_backup_removes_the_partial_file(self) -> None:
        start = datetime(2026, 1, 15, 9, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "activity.db"
            destination = root / "backup.db"
            with ActivityDatabase(source) as database:
                database.create_period(ActivityState("Code.exe", "Fictional"), start)
            locked = root / "locked"
            locked.mkdir()
            destination = locked / "backup.db"
            locked.chmod(0o500)
            try:
                with self.assertRaises(sqlite3.Error):
                    backup_activity_database(source, destination)
            finally:
                locked.chmod(0o700)
            self.assertFalse(destination.exists())
            self.assertFalse(Path(str(destination) + ".partial").exists())

            blocker = root / "not-a-directory"
            blocker.write_text("x", encoding="utf-8")
            with self.assertRaises(OSError):
                backup_activity_database(source, blocker / "backup.db")
            self.assertFalse(blocker.joinpath("backup.db.partial").exists())


if __name__ == "__main__":
    unittest.main()
