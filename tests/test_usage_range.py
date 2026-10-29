from __future__ import annotations

import unittest
from datetime import date, timedelta

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

    def test_seven_day_ranges_across_leap_days_and_year_boundaries(self) -> None:
        cases = [
            # (today, last_start, last_end, previous_start, previous_end)
            (date(2024, 3, 1), date(2024, 2, 24), date(2024, 3, 1), date(2024, 2, 17), date(2024, 2, 23)),
            (date(2025, 3, 1), date(2025, 2, 23), date(2025, 3, 1), date(2025, 2, 16), date(2025, 2, 22)),
            (date(2026, 1, 1), date(2025, 12, 26), date(2026, 1, 1), date(2025, 12, 19), date(2025, 12, 25)),
        ]
        for today, last_start, last_end, prev_start, prev_end in cases:
            with self.subTest(today=today.isoformat()):
                self.assertEqual(usage_analysis_range(today, "today"), (today, today))
                actual_last = usage_analysis_range(today, "week")
                actual_prev = usage_analysis_range(today, "previous-week")
                self.assertEqual(actual_last, (last_start, last_end))
                self.assertEqual(actual_prev, (prev_start, prev_end))

                # Each seven-day range contains seven inclusive calendar dates
                self.assertEqual((last_end - last_start).days + 1, 7)
                self.assertEqual((prev_end - prev_start).days + 1, 7)

                # No shared date and no gap between previous and current
                self.assertLess(prev_end, last_start)
                self.assertEqual((last_start - prev_end).days, 1)

                # Sanity: generate the dates and confirm length
                last_dates = [last_start + timedelta(days=i) for i in range(7)]
                prev_dates = [prev_start + timedelta(days=i) for i in range(7)]
                self.assertEqual(len(last_dates), 7)
                self.assertEqual(len(prev_dates), 7)
                self.assertEqual(set(last_dates) & set(prev_dates), set())


if __name__ == "__main__":
    unittest.main()
