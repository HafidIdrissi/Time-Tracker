from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from timetracker.database import ActivityDatabase, to_storage, to_utc
from timetracker.models import ActivityState


class DatabaseTimeTests(unittest.TestCase):
    def test_utc_conversion_and_storage_format(self) -> None:
        with self.assertRaises(ValueError):
            to_utc(datetime(2026, 1, 15, 12, 0))

        local = datetime(2026, 1, 15, 12, 30, tzinfo=timezone(timedelta(hours=2)))
        self.assertEqual(to_utc(local), datetime(2026, 1, 15, 10, 30, tzinfo=timezone.utc))
        stored = to_storage(local)
        self.assertEqual(stored, "2026-01-15T10:30:00.000+00:00")

    def test_end_before_start_is_clamped_and_unicode_round_trips(self) -> None:
        start = datetime(2026, 1, 15, 9, 0, tzinfo=timezone(timedelta(hours=-5)))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "activity.db"
            with ActivityDatabase(path) as database:
                active_id = database.create_period(
                    ActivityState("éditeur.exe", "Projet — été"), start
                )
                database.update_period(active_id, start, start - timedelta(minutes=5))
                idle_id = database.create_period(
                    ActivityState("Idle", "Pause café", is_idle=True),
                    start + timedelta(hours=1),
                )
                database.update_period(
                    idle_id,
                    start + timedelta(hours=1),
                    start + timedelta(hours=1, minutes=4),
                )
                periods = database.periods_between(
                    start - timedelta(days=1), start + timedelta(days=1)
                )

        self.assertEqual(periods[0].application, "éditeur.exe")
        self.assertEqual(periods[0].window_title, "Projet — été")
        self.assertEqual(periods[0].ended_at, to_utc(start))
        self.assertGreaterEqual(periods[0].ended_at, periods[0].started_at)
        self.assertEqual(periods[0].duration_seconds, 0)
        self.assertFalse(periods[0].is_idle)
        self.assertTrue(periods[1].is_idle)
        self.assertEqual(periods[1].window_title, "Pause café")
        self.assertEqual(periods[1].duration_seconds, 4 * 60)
        self.assertTrue(path.name == "activity.db")


if __name__ == "__main__":
    unittest.main()
