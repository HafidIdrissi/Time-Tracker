from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from timetracker.database import ActivityDatabase
from timetracker.models import ActivitySnapshot, ActivityState
from timetracker.tracker import ActivityTracker


class UnusedProvider:
    def sample(self) -> ActivitySnapshot:
        raise AssertionError("The polling loop is not used in this test")


class TrackerTests(unittest.TestCase):
    def test_window_changes_and_idle_threshold_create_precise_periods(self) -> None:
        origin = datetime(2026, 7, 20, 8, 0, tzinfo=timezone.utc)
        editor = ActivityState("Code.exe", "Local Time Tracker")
        browser = ActivityState("firefox.exe", "Documentation")

        with tempfile.TemporaryDirectory() as directory:
            with ActivityDatabase(Path(directory) / "activity.db") as database:
                tracker = ActivityTracker(database, UnusedProvider())
                tracker.record_snapshot(ActivitySnapshot(editor, 0), origin)
                tracker.record_snapshot(
                    ActivitySnapshot(editor, 179), origin + timedelta(seconds=179)
                )
                tracker.record_snapshot(
                    ActivitySnapshot(editor, 185), origin + timedelta(seconds=185)
                )
                tracker.record_snapshot(
                    ActivitySnapshot(browser, 0), origin + timedelta(seconds=190)
                )
                tracker.record_snapshot(
                    ActivitySnapshot(browser, 5), origin + timedelta(seconds=195)
                )

                periods = database.periods_between(
                    origin - timedelta(seconds=1), origin + timedelta(minutes=10)
                )

        self.assertEqual(len(periods), 3)
        self.assertEqual(periods[0].application, "Code.exe")
        self.assertEqual(periods[0].duration_seconds, 180)
        self.assertTrue(periods[1].is_idle)
        self.assertEqual(periods[1].duration_seconds, 10)
        self.assertEqual(periods[2].application, "firefox.exe")
        self.assertEqual(periods[2].duration_seconds, 5)


if __name__ == "__main__":
    unittest.main()

