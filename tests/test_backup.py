from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from timetracker.backup import backup_activity_database
from timetracker.database import ActivityDatabase
from timetracker.models import ActivityState


class BackupTests(unittest.TestCase):
    def _rows(self, path: Path, start: datetime) -> list[str]:
        with ActivityDatabase(path) as database:
            periods = database.periods_between(start - timedelta(days=1), start + timedelta(days=1))
        return [period.window_title for period in periods]

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
            copied = self._rows(destination, start)
            after = self._rows(source, start)
        self.assertEqual(copied, ["Fictional"])
        self.assertEqual(after, [period.window_title for period in original])
        self.assertEqual(original[0].duration_seconds, 180)

    def test_same_destination_is_rejected_while_the_source_stays_open(self) -> None:
        start = datetime(2026, 1, 15, 9, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "activity.db"
            with ActivityDatabase(source) as database:
                database.create_period(ActivityState("Code.exe", "Fictional"), start)
                with self.assertRaises(ValueError):
                    backup_activity_database(source, source)
                titles = [
                    period.window_title
                    for period in database.periods_between(
                        start - timedelta(days=1), start + timedelta(days=1)
                    )
                ]
            self.assertEqual(titles, ["Fictional"])
            self.assertTrue(source.read_bytes().startswith(b"SQLite format 3"))

    def test_failed_backup_preserves_existing_files(self) -> None:
        start = datetime(2026, 1, 15, 9, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "activity.db"
            destination = root / "backup.db"
            sibling = root / "backup.db.partial"
            sibling.write_text("keep this sibling", encoding="utf-8")
            with ActivityDatabase(source) as database:
                period_id = database.create_period(ActivityState("Code.exe", "Fictional"), start)
                database.update_period(period_id, start, start + timedelta(minutes=3))
            backup_activity_database(source, destination)

            real_connect = sqlite3.connect

            def connect(path, *args, **kwargs):  # type: ignore[no-untyped-def]
                if Path(path).resolve() != source.resolve():
                    raise sqlite3.DatabaseError("disk full")
                return real_connect(path, *args, **kwargs)

            with mock.patch("timetracker.backup.sqlite3.connect", side_effect=connect):
                with self.assertRaises(sqlite3.DatabaseError):
                    backup_activity_database(source, destination)

            self.assertEqual(self._rows(destination, start), ["Fictional"])
            self.assertEqual(sibling.read_text(encoding="utf-8"), "keep this sibling")
            self.assertEqual(list(root.glob(".backup.db.*.tmp")), [])

    def test_source_connection_failure_removes_only_its_temporary_file(self) -> None:
        start = datetime(2026, 1, 15, 9, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "activity.db"
            destination = root / "backup.db"
            with ActivityDatabase(source) as database:
                database.create_period(ActivityState("Code.exe", "Fictional"), start)
            destination.write_bytes(b"previous backup")
            with mock.patch(
                "timetracker.backup.sqlite3.connect",
                side_effect=sqlite3.OperationalError("source cannot be opened"),
            ):
                with self.assertRaises(sqlite3.OperationalError):
                    backup_activity_database(source, destination)
            self.assertEqual(destination.read_bytes(), b"previous backup")
            self.assertEqual(list(root.glob(".backup.db.*.tmp")), [])
            self.assertEqual(self._rows(source, start), ["Fictional"])

    def test_relative_and_absolute_aliases_are_rejected(self) -> None:
        start = datetime(2026, 4, 4, 8, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "activity.db"
            self._write_source(source, start)
            source_bytes = source.read_bytes()
            sibling = root / "keep.txt"
            sibling.write_text("leave me", encoding="utf-8")

            previous = Path.cwd()
            os.chdir(root)
            try:
                self._assert_alias_rejected(Path("activity.db"), source.resolve(), start, source_bytes, sibling)
            finally:
                os.chdir(previous)

            destination = root / "backup.db"
            backup_activity_database(source, destination)
            self.assertEqual(self._rows(destination, start), ["Fictional notes"])
            self.assertEqual(source.read_bytes(), source_bytes)
            self.assertEqual(sibling.read_text(encoding="utf-8"), "leave me")

    def test_hard_link_alias_is_rejected(self) -> None:
        self._assert_linked_alias_rejected(os.link, "hard link")

    def test_symlink_alias_is_rejected(self) -> None:
        self._assert_linked_alias_rejected(os.symlink, "symlink")

    def _write_source(self, source: Path, start: datetime) -> None:
        with ActivityDatabase(source) as database:
            period_id = database.create_period(ActivityState("notes.exe", "Fictional notes"), start)
            database.update_period(period_id, start, start + timedelta(minutes=4))

    def _assert_linked_alias_rejected(self, link: object, kind: str) -> None:
        start = datetime(2026, 4, 4, 8, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "activity.db"
            alias = root / "alias.db"
            self._write_source(source, start)
            source_bytes = source.read_bytes()
            sibling = root / "keep.txt"
            sibling.write_text("leave me", encoding="utf-8")
            try:
                link(source, alias)  # type: ignore[operator]
            except OSError as exc:
                self.skipTest(f"{kind} is not supported here: {exc}")
            self._assert_alias_rejected(source, alias, start, source_bytes, sibling)

    def _assert_alias_rejected(
        self,
        source: Path,
        destination: Path,
        start: datetime,
        source_bytes: bytes,
        sibling: Path,
    ) -> None:
        with self.assertRaises(ValueError) as caught:
            backup_activity_database(source, destination)
        self.assertIn("different file", str(caught.exception))
        self.assertEqual(source.read_bytes(), source_bytes)
        self.assertEqual(self._rows(source, start), ["Fictional notes"])
        self.assertEqual(sibling.read_text(encoding="utf-8"), "leave me")
        self.assertEqual(list(destination.parent.glob(f".{destination.name}.*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
