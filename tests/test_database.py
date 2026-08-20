from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from timetracker.database import ActivityDatabase
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


if __name__ == "__main__":
    unittest.main()
