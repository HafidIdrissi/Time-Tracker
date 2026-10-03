from __future__ import annotations

import unittest
from datetime import date

from timetracker.analytics import analyze_usage, usage_analysis_range


class UsageRangeTests(unittest.TestCase):
    def test_previous_seven_days_do_not_overlap_last_seven_days(self) -> None:
        today = date(2026, 9, 29)
        self.assertEqual(usage_analysis_range(today, "today"), (today, today))
        last_start, last_end = usage_analysis_range(today, "week")
        previous_start, previous_end = usage_analysis_range(today, "previous-week")
        self.assertEqual((last_start, last_end), (date(2026, 9, 23), date(2026, 9, 29)))
        self.assertEqual((previous_start, previous_end), (date(2026, 9, 16), date(2026, 9, 22)))
        self.assertLess(previous_end, last_start)
        empty = analyze_usage([], previous_start, previous_end)
        self.assertEqual(empty.active_seconds, 0)
        self.assertEqual(len(empty.buckets), 7)


if __name__ == "__main__":
    unittest.main()
