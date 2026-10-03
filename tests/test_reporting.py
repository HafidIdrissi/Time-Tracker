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
            category="Work",
            color="#4f46e5",
        )
        html = render_html([period], date(2026, 7, 20), date(2026, 7, 20))

        self.assertIn("Activity Report", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn('<script>alert("x")</script>', html)
        self.assertNotIn("https://", html)

    def test_empty_report_states_labels_unicode_and_offline_markup(self) -> None:
        empty = render_html([], date(2026, 7, 20), date(2026, 7, 20))
        self.assertIn("0 min", empty)
        self.assertIn("No activity during this period.", empty)
        self.assertIn("No activity", empty)
        self.assertIn("2026-07-20", empty)
        self.assertNotIn("from 2026-07-20 to 2026-07-20", empty)

        ranged = render_html([], date(2026, 7, 20), date(2026, 7, 22))
        self.assertIn("from 2026-07-20 to 2026-07-22", ranged)

        start = datetime(2026, 7, 20, 9, 0, tzinfo=timezone.utc).astimezone()
        period = ReportPeriod(
            application="éditeur.exe",
            window_title='Projet "été" <alpha> & beta',
            started_at=start,
            ended_at=start + timedelta(minutes=5),
            duration_seconds=300,
            is_idle=False,
            category="Travail",
            color="#4f46e5",
        )
        html = render_html([period], date(2026, 7, 20), date(2026, 7, 20))
        self.assertIn("éditeur.exe", html)
        self.assertIn("Travail", html)
        self.assertIn("été", html)
        self.assertIn("&amp;", html)
        self.assertIn("&lt;alpha&gt;", html)
        self.assertIn("&quot;", html)
        self.assertIn('title="', html)
        self.assertNotIn('title="Projet "été"', html)
        self.assertIn('<meta charset="utf-8">', html)
        self.assertIn("@media print", html)
        self.assertNotIn("http://", html)
        self.assertNotIn("https://", html)
        self.assertNotIn("<script", html)
        self.assertNotIn("<link", html)
        self.assertNotIn("url(", html)


if __name__ == "__main__":
    unittest.main()
