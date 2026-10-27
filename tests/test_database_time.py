from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone, tzinfo
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
    
    def test_recent_periods_tie_breaker_and_limit_validation(self) -> None:
        start = datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc)
        fixed_end = datetime(2026, 10, 1, 11, 0, tzinfo=timezone.utc)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "activity.db"
            with ActivityDatabase(path) as database:
                id1 = database.create_period(ActivityState("app1.exe", "Active App"), start)
                id2 = database.create_period(ActivityState("Idle", "Away", is_idle=True), start)
                id3 = database.create_period(ActivityState("app2.exe", "Another App"), start)

                database.update_period(id1, start, fixed_end)
                database.update_period(id2, start, fixed_end)
                database.update_period(id3, start, fixed_end)

                read_1 = database.recent_periods(limit=5)
                read_2 = database.recent_periods(limit=5)

                self.assertEqual(read_1, read_2)
                self.assertEqual([r.id for r in read_1], [id3, id2, id1])

                small_limit = database.recent_periods(limit=2)
                self.assertEqual(len(small_limit), 2)
                self.assertEqual([r.id for r in small_limit], [id3, id2])

                large_limit = database.recent_periods(limit=100)
                self.assertEqual(len(large_limit), 3)

                with self.assertRaises(ValueError):
                    database.recent_periods(limit=0)

                with self.assertRaises(ValueError):
                    database.recent_periods(limit=-1)


class _OffsetlessTzinfo(tzinfo):
    """Aware tzinfo that deliberately returns None from utcoffset()."""

    def utcoffset(self, dt):  # type: ignore[override]
        return None

    def dst(self, dt):  # type: ignore[override]
        return None

    def tzname(self, dt):  # type: ignore[override]
        return "OFFSETLESS"


class DatabaseOffsetlessTzinfoTests(unittest.TestCase):
    def test_to_utc_and_to_storage_reject_offsetless_tzinfo(self) -> None:
        offsetless = datetime(2026, 3, 1, 12, 0, tzinfo=_OffsetlessTzinfo())
        with self.assertRaises(ValueError) as raised:
            to_utc(offsetless)
        self.assertIn("timezone-aware", str(raised.exception))
        with self.assertRaises(ValueError):
            to_storage(offsetless)

    def test_create_period_rejects_offsetless_without_mutation(self) -> None:
        start = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)
        offsetless = datetime(2026, 3, 1, 13, 0, tzinfo=_OffsetlessTzinfo())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "activity.db"
            with ActivityDatabase(path) as database:
                ok_id = database.create_period(ActivityState("ok.exe", "Valid"), start)
                with self.assertRaises(ValueError):
                    database.create_period(ActivityState("bad.exe", "Offsetless"), offsetless)
                with self.assertRaises(ValueError):
                    database.periods_between(offsetless, start + timedelta(hours=1))
                periods = database.recent_periods(limit=10)
                self.assertEqual([p.id for p in periods], [ok_id])
                self.assertEqual(periods[0].application, "ok.exe")


if __name__ == "__main__":
    unittest.main()
