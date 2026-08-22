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

    def test_browser_title_hyphen_en_dash_em_dash_suffixes(self) -> None:
        """Cover hyphen, en dash, and em dash suffixes for each supported browser."""
        cases = [
            ("chrome.exe", "Inbox - Google Chrome", "Inbox"),
            ("chrome.exe", "Inbox – Google Chrome", "Inbox"),
            ("chrome.exe", "Inbox — Google Chrome", "Inbox"),
            ("firefox.exe", "Docs - Mozilla Firefox", "Docs"),
            ("firefox.exe", "Docs – Mozilla Firefox", "Docs"),
            ("firefox.exe", "Docs — Mozilla Firefox", "Docs"),
            ("msedge.exe", "News - Microsoft Edge", "News"),
            ("msedge.exe", "News – Microsoft Edge", "News"),
            ("msedge.exe", "News — Microsoft Edge", "News"),
            ("brave.exe", "Search - Brave", "Search"),
            ("brave.exe", "Search – Brave", "Search"),
            ("brave.exe", "Search — Brave", "Search"),
            ("opera.exe", "Mail - Opera", "Mail"),
            ("opera.exe", "Mail – Opera", "Mail"),
            ("opera.exe", "Mail — Opera", "Mail"),
            ("opera_gx.exe", "Stream - Opera", "Stream"),
            ("opera_gx.exe", "Stream – Opera", "Stream"),
            ("opera_gx.exe", "Stream — Opera", "Stream"),
            ("vivaldi.exe", "Notes - Vivaldi", "Notes"),
            ("vivaldi.exe", "Notes – Vivaldi", "Notes"),
            ("vivaldi.exe", "Notes — Vivaldi", "Notes"),
        ]
        for application, window_title, expected in cases:
            with self.subTest(application=application, window_title=window_title):
                self.assertEqual(browser_tab_title(application, window_title), expected)

    def test_browser_title_case_insensitive_executable(self) -> None:
        self.assertEqual(
            browser_tab_title("Chrome.EXE", "Gmail - Google Chrome"),
            "Gmail",
        )
        self.assertEqual(
            browser_tab_title("MsEdge.Exe", "Work – Microsoft Edge"),
            "Work",
        )

    def test_browser_title_empty_tab_is_untitled(self) -> None:
        self.assertEqual(
            browser_tab_title("firefox.exe", "   "),
            "(Untitled tab)",
        )
        self.assertEqual(
            browser_tab_title("chrome.exe", ""),
            "(Untitled tab)",
        )

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
