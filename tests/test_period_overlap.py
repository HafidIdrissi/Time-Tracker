from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from timetracker.database import ActivityDatabase
from timetracker.models import ActivityState


class PeriodOverlapTests(unittest.TestCase):
    def test_half_open_overlap_and_order_without_clipping(self) -> None:
        origin = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)
        range_start = origin + timedelta(hours=2)
        range_end = origin + timedelta(hours=4)
        editor = ActivityState("Code.exe", "Fictional editor")

        with tempfile.TemporaryDirectory() as directory:
            with ActivityDatabase(Path(directory) / "activity.db") as database:
                def add(start: datetime, end: datetime) -> None:
                    period_id = database.create_period(editor, start)
                    database.update_period(period_id, start, end)

                add(origin, origin + timedelta(minutes=30))
                add(origin + timedelta(hours=1), range_start)
                crossing_start = (origin + timedelta(hours=1), range_start + timedelta(minutes=20))
                inside = (range_start + timedelta(minutes=10), range_start + timedelta(hours=1))
                same_start_later = (inside[0], inside[0] + timedelta(minutes=15))
                crossing_end = (range_end - timedelta(minutes=15), range_end + timedelta(minutes=15))
                add(range_end, range_end + timedelta(minutes=20))
                for start, end in (
                    crossing_start,
                    inside,
                    same_start_later,
                    crossing_end,
                ):
                    add(start, end)

                found = database.periods_between(range_start, range_end)

        self.assertEqual(
            [(period.started_at, period.ended_at) for period in found],
            [crossing_start, inside, same_start_later, crossing_end],
        )
        self.assertEqual([period.id for period in found], sorted(period.id for period in found))
        self.assertLess(found[1].id, found[2].id)
        self.assertEqual(found[2].started_at, inside[0])
        self.assertEqual(found[2].ended_at, same_start_later[1])

    def test_reversed_and_empty_bounds_are_validated_before_sql(self) -> None:
        start = datetime(2026, 3, 4, 12, 0, tzinfo=timezone.utc)
        same_instant = datetime(2026, 3, 4, 13, 0, tzinfo=timezone(timedelta(hours=1)))
        earlier = start - timedelta(minutes=1)
        naive = datetime(2026, 3, 4, 12, 0)

        with tempfile.TemporaryDirectory() as directory:
            with ActivityDatabase(Path(directory) / "activity.db") as database:
                statements: list[str] = []
                database.connection.set_trace_callback(statements.append)
                try:
                    with self.assertRaises(ValueError) as reversed_bounds:
                        database.periods_between(start, earlier)
                    self.assertIn("precede", str(reversed_bounds.exception))

                    self.assertEqual(database.periods_between(start, start), [])
                    self.assertEqual(database.periods_between(start, same_instant), [])
                    self.assertEqual(statements, [])

                    found = database.periods_between(earlier, start)
                    self.assertEqual(found, [])
                    self.assertEqual(len(statements), 1)

                    with self.assertRaises(ValueError) as unaware:
                        database.periods_between(naive, start)
                    self.assertIn("timezone-aware", str(unaware.exception))
                    self.assertEqual(len(statements), 1)
                finally:
                    database.connection.set_trace_callback(None)


if __name__ == "__main__":
    unittest.main()
