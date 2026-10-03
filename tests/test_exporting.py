from __future__ import annotations

import csv
import json
import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
