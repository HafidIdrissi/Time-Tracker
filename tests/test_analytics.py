from __future__ import annotations

import unittest
from datetime import date, datetime, timedelta, timezone

from timetracker.analytics import analyze_usage, browser_tab_title
from timetracker.reporting import ReportPeriod


class AnalyticsTests(unittest.TestCase):
    def _period(
        self,
        start: datetime,
        minutes: int,
        application: str,
        title: str,
        category: str,
        color: str,
        idle: bool = False,
    ) -> ReportPeriod:
        return ReportPeriod(
            application=application,
            window_title=title,
            started_at=start,
            ended_at=start + timedelta(minutes=minutes),
            duration_seconds=minutes * 60,
            is_idle=idle,
            category=category,
            color=color,
        )

    def test_browser_titles_are_cleaned(self) -> None:
        self.assertEqual(
            browser_tab_title("chrome.exe", "Gmail - Google Chrome"),
            "Gmail",
        )
        self.assertIsNone(browser_tab_title("Code.exe", "Project"))

    def test_usage_is_grouped_by_category_application_and_tab(self) -> None:
        start = datetime(2026, 7, 20, 9, 0, tzinfo=timezone.utc).astimezone()
        periods = [
            self._period(start, 20, "chrome.exe", "Gmail - Google Chrome", "Work", "#111111"),
            self._period(start + timedelta(minutes=20), 10, "chrome.exe", "Gmail - Google Chrome", "Work", "#111111"),
            self._period(start + timedelta(minutes=30), 15, "TslGame.exe", "PUBG", "Games", "#222222"),
            self._period(start + timedelta(minutes=45), 5, "Idle", "Break", "Idle", "#999999", idle=True),
        ]

        analytics = analyze_usage(periods, date(2026, 7, 20), date(2026, 7, 20))

        self.assertEqual(analytics.active_seconds, 45 * 60)
        self.assertEqual(analytics.idle_seconds, 5 * 60)
        self.assertEqual(analytics.categories[0], ("Work", "#111111", 30 * 60))
        self.assertEqual(analytics.applications[0], ("chrome.exe", 30 * 60))
        self.assertEqual(analytics.browser_tabs[0], ("chrome.exe", "Gmail", 30 * 60))
        self.assertEqual(analytics.longest_session_seconds, 45 * 60)
        self.assertEqual(len(analytics.buckets), 24)

    def test_weekly_average_includes_calendar_days_without_activity(self) -> None:
        start = datetime(2026, 7, 20, 9, 0, tzinfo=timezone.utc).astimezone()
        periods = [
            self._period(start, 70, "Code.exe", "Project", "Work", "#111111")
        ]

        analytics = analyze_usage(periods, date(2026, 7, 20), date(2026, 7, 26))

        self.assertEqual(analytics.average_daily_seconds, 10 * 60)
        self.assertEqual(len(analytics.buckets), 7)


if __name__ == "__main__":
    unittest.main()
