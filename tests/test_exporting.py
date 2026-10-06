from __future__ import annotations

import csv
import json
import sqlite3
import tempfile
import unittest
from unittest import mock
from datetime import datetime, timedelta, timezone
from pathlib import Path

from timetracker.database import ActivityDatabase
from timetracker.exporting import EXPORT_FIELDS, export_activity
from timetracker.models import ActivityState


class ExportTests(unittest.TestCase):
    def _database(self, directory: Path) -> Path:
        path = directory / "activity.db"
        start = datetime(2026, 1, 15, 9, 0, tzinfo=timezone(timedelta(hours=1)))
        with ActivityDatabase(path) as database:
            period_id = database.create_period(
                ActivityState("notes.exe", 'Hello, "world"\nnext'), start
            )
            database.update_period(period_id, start, start + timedelta(minutes=5))
            idle_id = database.create_period(
                ActivityState("Idle", "Pause", is_idle=True), start + timedelta(minutes=5)
            )
            database.update_period(
                idle_id,
                start + timedelta(minutes=5),
                start + timedelta(minutes=6),
            )
        return path

    def test_csv_and_json_round_trip_without_changing_the_database(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self._database(root)

            def snapshot() -> list[tuple[str, str, float, bool]]:
                with ActivityDatabase(source) as database:
                    return [
                        (period.application, period.window_title, period.duration_seconds, period.is_idle)
                        for period in database.all_periods()
                    ]

            before = snapshot()
            csv_path = export_activity(source, root / "out.csv", "csv")
            json_path = export_activity(source, root / "out.json", "json")

            with csv_path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(list(rows[0]), list(EXPORT_FIELDS))
            self.assertEqual(rows[0]["application"], "notes.exe")
            self.assertIn("Hello, \"world\"", rows[0]["window_title"])
            self.assertIn("\n", rows[0]["window_title"])
            self.assertIn("+", rows[0]["started_at"])
            self.assertEqual(rows[1]["is_idle"], "True")

            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload[0]["window_title"], 'Hello, "world"\nnext')
            self.assertTrue(payload[1]["is_idle"])
            self.assertIn("+", payload[0]["ended_at"])
            self.assertEqual(snapshot(), before)

    def test_empty_database_and_failed_export_leave_no_partial_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            missing = root / "missing.db"
            csv_path = export_activity(missing, root / "empty.csv", "csv")
            self.assertEqual(csv_path.read_text(encoding="utf-8").strip(), ",".join(EXPORT_FIELDS))
            self.assertFalse(missing.exists())

            blocker = root / "blocker"
            blocker.write_text("not a directory", encoding="utf-8")
            with self.assertRaises(OSError):
                export_activity(missing, blocker / "export.json", "json")
            self.assertFalse((blocker / "export.json.partial").exists())
            self.assertFalse((blocker / "export.json").exists())

    def test_destination_cannot_replace_the_source_database(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = self._database(Path(directory))
            with self.assertRaises(ValueError):
                export_activity(source, source, "json")
            with ActivityDatabase(source) as database:
                rows = database.all_periods()
            self.assertEqual(rows[0].application, "notes.exe")
            self.assertTrue(source.read_bytes().startswith(b"SQLite format 3"))

    def test_existing_partial_sibling_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self._database(root)
            sibling = root / "out.json.partial"
            sibling.write_text("keep this sibling", encoding="utf-8")
            export_activity(source, root / "out.json", "json")
            self.assertEqual(sibling.read_text(encoding="utf-8"), "keep this sibling")
            self.assertTrue((root / "out.json").is_file())

    def test_unsupported_formats_exit_before_touching_the_filesystem(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "activity.db"
            source.write_bytes(b"not a database")
            destination = root / "missing" / "out.csv"
            existing = root / "kept.json"
            existing.write_text("leave me", encoding="utf-8")

            with mock.patch(
                "timetracker.exporting.ActivityDatabase",
                side_effect=AssertionError("database opened"),
            ) as database_type:
                for file_format in ("", "xml"):
                    with self.assertRaises(ValueError) as caught:
                        export_activity(source, destination, file_format)
                    message = str(caught.exception)
                    self.assertIn("csv", message)
                    self.assertIn("json", message)

            database_type.assert_not_called()
            self.assertFalse((root / "missing").exists())
            self.assertEqual(existing.read_text(encoding="utf-8"), "leave me")
            self.assertEqual(source.read_bytes(), b"not a database")
            self.assertEqual(list(root.glob("**/*.tmp")), [])

    def test_mixed_case_csv_and_json_names_are_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self._database(root)
            csv_path = export_activity(source, root / "out.csv", "CSV")
            json_path = export_activity(source, root / "out.json", "Json")
            self.assertTrue(csv_path.read_text(encoding="utf-8").startswith("application,"))
            self.assertTrue(json_path.read_text(encoding="utf-8").lstrip().startswith("["))

    def test_export_includes_committed_rows_still_in_the_wal(self) -> None:
        start = datetime(2026, 2, 2, 10, 0, tzinfo=timezone.utc)
        idle_start = start + timedelta(minutes=20)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "activity.db"
            writer = ActivityDatabase(source)
            try:
                writer.connection.execute("PRAGMA wal_autocheckpoint = 0")
                active_id = writer.create_period(ActivityState("notes.exe", "Fictional notes"), start)
                writer.update_period(active_id, start, idle_start)
                idle_id = writer.create_period(ActivityState("Idle", "Pause", is_idle=True), idle_start)
                writer.update_period(idle_id, idle_start, idle_start + timedelta(minutes=5))

                wal_path = Path(str(source) + "-wal")
                self.assertGreater(wal_path.stat().st_size, 32)
                main_only = root / "main-only.db"
                main_only.write_bytes(source.read_bytes())
                with sqlite3.connect(main_only) as isolated:
                    isolated_rows = isolated.execute(
                        "SELECT COUNT(*) FROM sqlite_master WHERE name = 'activity_periods'"
                    ).fetchone()
                    if isolated_rows[0]:
                        committed_in_main = isolated.execute(
                            "SELECT COUNT(*) FROM activity_periods"
                        ).fetchone()[0]
                    else:
                        committed_in_main = 0
                self.assertEqual(committed_in_main, 0)

                csv_path = export_activity(source, root / "out.csv", "csv")
                json_path = export_activity(source, root / "out.json", "json")
                with csv_path.open(encoding="utf-8", newline="") as handle:
                    csv_rows = list(csv.DictReader(handle))
                json_rows = json.loads(json_path.read_text(encoding="utf-8"))
                self.assertEqual(
                    [(row["application"], row["window_title"], row["duration_seconds"], row["is_idle"]) for row in csv_rows],
                    [("notes.exe", "Fictional notes", "1200.0", "False"), ("Idle", "Pause", "300.0", "True")],
                )
                self.assertEqual(
                    [(row["application"], row["window_title"], row["duration_seconds"], row["is_idle"]) for row in json_rows],
                    [("notes.exe", "Fictional notes", 1200.0, False), ("Idle", "Pause", 300.0, True)],
                )

                later_id = writer.create_period(
                    ActivityState("calendar.exe", "Fictional calendar"),
                    idle_start + timedelta(minutes=5),
                )
                self.assertGreater(later_id, idle_id)
                self.assertEqual(len(writer.all_periods()), 3)
            finally:
                writer.close()
            self.assertEqual(list(root.glob("**/*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
