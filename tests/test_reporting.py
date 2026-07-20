from __future__ import annotations

import unittest
from datetime import date, datetime, timedelta, timezone

from timetracker.reporting import ReportPeriod, format_duration, render_html


class ReportingTests(unittest.TestCase):
    def test_duration_formatting(self) -> None:
        self.assertEqual(format_duration(0), "0 min")
        self.assertEqual(format_duration(20), "< 1 min")
        self.assertEqual(format_duration(65 * 60), "1 h 05 min")

    def test_html_is_standalone_and_escapes_window_titles(self) -> None:
        start = datetime(2026, 7, 20, 9, 0, tzinfo=timezone.utc).astimezone()
        period = ReportPeriod(
            application="browser.exe",
            window_title='<script>alert("x")</script>',
            started_at=start,
            ended_at=start + timedelta(minutes=30),
            duration_seconds=1800,
            is_idle=False,
            category="Travail",
            color="#4f46e5",
        )
        html = render_html([period], date(2026, 7, 20), date(2026, 7, 20))

        self.assertIn("Rapport d'activité", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn('<script>alert("x")</script>', html)
        self.assertNotIn("https://", html)


if __name__ == "__main__":
    unittest.main()

