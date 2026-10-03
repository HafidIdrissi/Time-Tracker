from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from timetracker.categories import Categorizer, Category
from timetracker.database import ActivityDatabase
from timetracker.models import ActivityState
from timetracker.reporting import collect_periods


class ReportClippingTests(unittest.TestCase):
    def test_periods_are_clipped_to_the_selected_range(self) -> None:
        zone = timezone(timedelta(hours=1))
        range_start = datetime(2026, 1, 15, 0, 0, tzinfo=zone)
        range_end = datetime(2026, 1, 16, 0, 0, tzinfo=zone)
        categorizer = Categorizer([Category("Work", "#112233", ("code.exe",))])

        with tempfile.TemporaryDirectory() as directory:
            with ActivityDatabase(Path(directory) / "activity.db") as database:
                def add(state: ActivityState, start: datetime, end: datetime) -> None:
                    period_id = database.create_period(state, start)
                    database.update_period(period_id, start, end)

                add(
                    ActivityState("Code.exe", "Before"),
                    range_start - timedelta(minutes=30),
                    range_start + timedelta(minutes=20),
                )
                add(
                    ActivityState("Code.exe", "After"),
                    range_end - timedelta(minutes=15),
                    range_end + timedelta(minutes=40),
                )
                add(
                    ActivityState("Code.exe", "Spanning"),
                    range_start - timedelta(hours=2),
                    range_end + timedelta(hours=3),
                )
                add(
                    ActivityState("Code.exe", "Empty"),
                    range_start + timedelta(hours=12),
                    range_start + timedelta(hours=12),
                )
                add(
                    ActivityState("Code.exe", "Private title", is_idle=True),
                    range_start + timedelta(hours=1),
                    range_start + timedelta(hours=1, minutes=10),
                )
                periods = collect_periods(database, categorizer, range_start, range_end)

        self.assertEqual(len(periods), 4)
        spanning, before, idle, after = periods
        self.assertEqual(before.started_at, range_start.astimezone())
        self.assertEqual(before.ended_at, (range_start + timedelta(minutes=20)).astimezone())
        self.assertEqual(before.duration_seconds, 20 * 60)
        self.assertEqual(before.category, "Work")
        self.assertEqual(after.ended_at, range_end.astimezone())
        self.assertEqual(after.duration_seconds, 15 * 60)
        self.assertEqual(spanning.started_at, range_start.astimezone())
        self.assertEqual(spanning.ended_at, range_end.astimezone())
        self.assertEqual(spanning.duration_seconds, (range_end - range_start).total_seconds())
        self.assertEqual(idle.application, "Idle")
        self.assertEqual(idle.window_title, "No keyboard or mouse activity")
        self.assertEqual(idle.category, "Idle")
        self.assertTrue(idle.is_idle)
        self.assertNotIn("Private title", idle.window_title)


if __name__ == "__main__":
    unittest.main()
