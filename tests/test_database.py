from __future__ import annotations

import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from timetracker.database import ActivityDatabase, to_storage
from timetracker.models import ActivityState


class DatabaseTests(unittest.TestCase):
    def test_recent_periods_and_clear(self) -> None:
        origin = datetime(2026, 7, 20, 8, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            with ActivityDatabase(Path(directory) / "activity.db") as database:
                first_id = database.create_period(ActivityState("Code.exe", "Project"), origin)
                database.update_period(first_id, origin, origin + timedelta(seconds=20))
                second_id = database.create_period(
                    ActivityState("chrome.exe", "Documentation"),
                    origin + timedelta(seconds=20),
                )
                database.update_period(
                    second_id,
                    origin + timedelta(seconds=20),
                    origin + timedelta(seconds=50),
                )

                recent = database.recent_periods(limit=1)
                self.assertEqual(len(recent), 1)
                self.assertEqual(recent[0].application, "chrome.exe")

                database.clear_periods()
                self.assertEqual(database.recent_periods(), [])

    def test_committed_activity_is_visible_to_a_second_connection(self) -> None:
        started = datetime(2026, 8, 1, 9, 0, tzinfo=timezone.utc)
        ended = started + timedelta(minutes=12)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "activity.db"
            writer = ActivityDatabase(path)
            try:
                period_id = writer.create_period(
                    ActivityState("notes.exe", "Fictional notes"), started
                )
                created = self._read_period(path, period_id)
                self.assertEqual(created["application"], "notes.exe")
                self.assertEqual(created["started_at"], to_storage(started))
                self.assertEqual(created["ended_at"], to_storage(started))
                self.assertEqual(created["duration_seconds"], 0)

                writer.update_period(period_id, started, ended)
                updated = self._read_period(path, period_id)
                self.assertEqual(updated["ended_at"], to_storage(ended))
                self.assertEqual(updated["duration_seconds"], 720)
            finally:
                writer.close()

            with ActivityDatabase(path) as reopened:
                periods = reopened.all_periods()
        self.assertEqual(len(periods), 1)
        self.assertEqual(periods[0].application, "notes.exe")
        self.assertEqual(periods[0].ended_at, ended)
        self.assertEqual(periods[0].duration_seconds, 720)

    def _read_period(self, path: Path, period_id: int) -> sqlite3.Row:
        reader = sqlite3.connect(path)
        try:
            reader.row_factory = sqlite3.Row
            row = reader.execute(
                """
                SELECT application, started_at, ended_at, duration_seconds
                FROM activity_periods
                WHERE id = ?
                """,
                (period_id,),
            ).fetchone()
        finally:
            reader.close()
        self.assertIsNotNone(row)
        return row

    def test_context_exit_closes_the_connection_when_the_body_raises(self) -> None:
        started = datetime(2026, 5, 6, 9, 30, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "activity.db"
            database = ActivityDatabase(path)
            with self.assertRaises(RuntimeError) as caught:
                with database:
                    period_id = database.create_period(
                        ActivityState("notes.exe", "Fictional notes"), started
                    )
                    database.update_period(period_id, started, started + timedelta(minutes=8))
                    raise RuntimeError("sentinel failure")
            self.assertEqual(str(caught.exception), "sentinel failure")
            with self.assertRaises(sqlite3.ProgrammingError):
                database.all_periods()

            with ActivityDatabase(path) as reader:
                periods = reader.all_periods()
        self.assertEqual(len(periods), 1)
        self.assertEqual(periods[0].application, "notes.exe")
        self.assertEqual(periods[0].window_title, "Fictional notes")
        self.assertEqual(periods[0].duration_seconds, 480)


if __name__ == "__main__":
    unittest.main()
