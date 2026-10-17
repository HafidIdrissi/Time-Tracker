from __future__ import annotations

import unittest
from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

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

    def test_browser_title_empty_or_suffix_only_is_untitled(self) -> None:
        self.assertEqual(
            browser_tab_title("chrome.exe", " - Google Chrome"),
            "(Untitled tab)",
        )
        self.assertEqual(
            browser_tab_title("chrome.exe", "- Google Chrome"),
            "(Untitled tab)",
        )
        self.assertEqual(
            browser_tab_title("firefox.exe", " – Mozilla Firefox"),
            "(Untitled tab)",
        )
        self.assertEqual(
            browser_tab_title("msedge.exe", " — Microsoft Edge"),
            "(Untitled tab)",
        )
        self.assertEqual(
            browser_tab_title("brave.exe", " - Brave"),
            "(Untitled tab)",
        )
        self.assertEqual(
            browser_tab_title("opera.exe", " - Opera"),
            "(Untitled tab)",
        )
        self.assertEqual(
            browser_tab_title("vivaldi.exe", " - Vivaldi"),
            "(Untitled tab)",
        )
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

    def test_rankings_break_duration_ties_deterministically(self) -> None:
        start = datetime(2026, 7, 20, 9, 0).astimezone()
        tied = [
            self._period(start, 10, "msedge.exe", "Notes - Microsoft Edge", "zeta", "#00ff00"),
            self._period(start, 10, "chrome.exe", "Inbox - Google Chrome", "Alpha", "#0000ff"),
            self._period(start, 10, "firefox.exe", "Other - Mozilla Firefox", "alpha", "#ffffff"),
        ]
        day = start.date()
        forward = analyze_usage(tied, day, day)
        reverse = analyze_usage(list(reversed(tied)), day, day)

        self.assertEqual(
            [(name, color) for name, color, _seconds in forward.categories],
            [("Alpha", "#0000ff"), ("alpha", "#ffffff"), ("zeta", "#00ff00")],
        )
        self.assertEqual(
            [name for name, _seconds in forward.applications],
            ["chrome.exe", "firefox.exe", "msedge.exe"],
        )
        self.assertEqual(
            [(application, title) for application, title, _seconds in forward.browser_tabs],
            [
                ("chrome.exe", "Inbox"),
                ("firefox.exe", "Other"),
                ("msedge.exe", "Notes"),
            ],
        )
        occupied = next(bucket for bucket in forward.buckets if bucket.categories)
        reverse_occupied = next(bucket for bucket in reverse.buckets if bucket.categories)
        self.assertEqual(
            [name for name, _color, _seconds in occupied.categories],
            ["Alpha", "alpha", "zeta"],
        )
        self.assertEqual(forward.categories, reverse.categories)
        self.assertEqual(forward.applications, reverse.applications)
        self.assertEqual(forward.browser_tabs, reverse.browser_tabs)
        self.assertEqual(occupied.categories, reverse_occupied.categories)
        self.assertEqual(forward.active_seconds, reverse.active_seconds)

    def test_case_equivalent_names_keep_a_stable_original_order(self) -> None:
        start = datetime(2026, 7, 20, 9, 0).astimezone()
        tied = [
            self._period(start, 10, "code.exe", "Editor", "work", "#aabbcc"),
            self._period(start, 10, "Code.exe", "Editor", "Work", "#AABBCC"),
            self._period(start, 10, "chrome.exe", "inbox - Google Chrome", "Mail", "#111111"),
            self._period(start, 10, "chrome.exe", "Inbox - Google Chrome", "Mail", "#111111"),
        ]
        day = start.date()
        forward = analyze_usage(tied, day, day)
        reverse = analyze_usage(list(reversed(tied)), day, day)
        self.assertEqual(
            [name for name, _seconds in forward.applications],
            ["chrome.exe", "Code.exe", "code.exe"],
        )
        self.assertEqual(
            [(name, color) for name, color, _seconds in forward.categories],
            [("Mail", "#111111"), ("Work", "#AABBCC"), ("work", "#aabbcc")],
        )
        self.assertEqual(
            [(application, title) for application, title, _seconds in forward.browser_tabs],
            [("chrome.exe", "Inbox"), ("chrome.exe", "inbox")],
        )
        self.assertEqual(forward.applications, reverse.applications)
        self.assertEqual(forward.categories, reverse.categories)
        self.assertEqual(forward.browser_tabs, reverse.browser_tabs)

    def _session(self, periods: list[ReportPeriod]) -> float:
        if not periods:
            return analyze_usage([], date(2026, 7, 20), date(2026, 7, 20)).longest_session_seconds
        start_day = min(period.started_at for period in periods).date()
        end_day = max(period.ended_at for period in periods).date()
        return analyze_usage(periods, start_day, end_day).longest_session_seconds

    def test_longest_session_boundaries(self) -> None:
        origin = datetime(2026, 7, 20, 9, 0, tzinfo=timezone.utc)
        active = self._period(origin, 10, "Code.exe", "Editor", "Work", "#111111")
        self.assertEqual(self._session([]), 0)
        self.assertEqual(self._session([active]), 10 * 60)

        continued = self._period(
            origin + timedelta(minutes=10, seconds=30),
            5,
            "Code.exe",
            "Editor",
            "Work",
            "#111111",
        )
        self.assertEqual(self._session([active, continued]), 15 * 60 + 30)

        split = self._period(
            origin + timedelta(minutes=10, seconds=31),
            5,
            "Code.exe",
            "Editor",
            "Work",
            "#111111",
        )
        self.assertEqual(self._session([active, split]), 10 * 60)

        idle = self._period(
            origin + timedelta(minutes=10),
            1,
            "Idle",
            "Break",
            "Idle",
            "#999999",
            idle=True,
        )
        after_idle = self._period(
            origin + timedelta(minutes=11),
            4,
            "Code.exe",
            "Editor",
            "Work",
            "#111111",
        )
        self.assertEqual(self._session([active, idle, after_idle]), 10 * 60)

        overlap = self._period(origin + timedelta(minutes=5), 10, "Code.exe", "Editor", "Work", "#111111")
        self.assertEqual(self._session([active, overlap]), 15 * 60)
        self.assertEqual(self._session([overlap, active]), 15 * 60)

    def test_hourly_and_daily_bucket_boundaries(self) -> None:
        day = date(2026, 1, 15)
        empty = analyze_usage([], day, day)
        self.assertEqual(len(empty.buckets), 24)
        self.assertEqual([bucket.label for bucket in empty.buckets], [f"{hour:02d} h" for hour in range(24)])

        start = datetime(2026, 1, 15, 10, 50).astimezone()
        crossing = self._period(start, 20, "Code.exe", "Editor", "Work", "#111111")
        hourly = analyze_usage([crossing], day, day)
        self.assertEqual(hourly.buckets[10].total_seconds, 10 * 60)
        self.assertEqual(hourly.buckets[11].total_seconds, 10 * 60)
        self.assertEqual(sum(bucket.total_seconds for bucket in hourly.buckets), hourly.active_seconds)

        idle = self._period(
            datetime(2026, 1, 15, 12, 0).astimezone(),
            30,
            "Idle",
            "Break",
            "Idle",
            "#999999",
            idle=True,
        )
        with_idle = analyze_usage([crossing, idle], day, day)
        self.assertEqual(with_idle.buckets[12].total_seconds, 0)
        self.assertEqual(sum(bucket.total_seconds for bucket in with_idle.buckets), with_idle.active_seconds)

        week = analyze_usage([], date(2026, 1, 15), date(2026, 1, 17))
        self.assertEqual(len(week.buckets), 3)

        late = datetime(2026, 1, 15, 23, 30).astimezone()
        overnight = self._period(late, 60, "Code.exe", "Editor", "Work", "#111111")
        daily = analyze_usage([overnight], date(2026, 1, 15), date(2026, 1, 16))
        self.assertEqual(len(daily.buckets), 2)
        self.assertEqual(daily.buckets[0].total_seconds, 30 * 60)
        self.assertEqual(daily.buckets[1].total_seconds, 30 * 60)
        self.assertEqual(sum(bucket.total_seconds for bucket in daily.buckets), daily.active_seconds)


    def test_idle_only_single_day_has_no_active_analytics(self) -> None:
        day = date(2026, 7, 20)
        fixed_timezone = timezone(timedelta(hours=5, minutes=30))

        def fixed_local_midnight(value: date) -> datetime:
            return datetime.combine(value, datetime.min.time(), tzinfo=fixed_timezone)

        idle_periods = [
            self._period(
                datetime(2026, 7, 20, 9, 0, tzinfo=fixed_timezone),
                5,
                "Idle",
                "Break",
                "Idle",
                "#999999",
                idle=True,
            ),
            self._period(
                datetime(2026, 7, 20, 14, 0, tzinfo=fixed_timezone),
                7,
                "Idle",
                "Away",
                "Idle",
                "#999999",
                idle=True,
            ),
        ]

        with patch(
            "timetracker.analytics.local_midnight",
            side_effect=fixed_local_midnight,
        ):
            analytics = analyze_usage(idle_periods, day, day)

            self.assertEqual(analytics.idle_seconds, 12 * 60)
            self.assertEqual(analytics.active_seconds, 0)
            self.assertEqual(analytics.average_daily_seconds, 0)
            self.assertEqual(analytics.longest_session_seconds, 0)
            self.assertEqual(analytics.categories, ())
            self.assertEqual(analytics.applications, ())
            self.assertEqual(analytics.browser_tabs, ())
            self.assertEqual(len(analytics.buckets), 24)

            for bucket in analytics.buckets:
                with self.subTest(bucket=bucket.label):
                    self.assertEqual(bucket.total_seconds, 0)
                    self.assertEqual(bucket.categories, ())

            active_control = self._period(
                datetime(2026, 7, 20, 10, 0, tzinfo=fixed_timezone),
                1,
                "Code.exe",
                "Editor",
                "Work",
                "#111111",
            )
            control = analyze_usage([active_control], day, day)

            self.assertEqual(control.active_seconds, 60)
            self.assertEqual(control.categories, (("Work", "#111111", 60),))
            self.assertEqual(control.applications, (("Code.exe", 60),))
            self.assertEqual(control.longest_session_seconds, 60)

    def test_idle_only_multi_day_has_no_active_analytics(self) -> None:
        start_day = date(2026, 7, 20)
        end_day = date(2026, 7, 22)
        fixed_timezone = timezone(timedelta(hours=5, minutes=30))

        def fixed_local_midnight(value: date) -> datetime:
            return datetime.combine(value, datetime.min.time(), tzinfo=fixed_timezone)

        idle_periods = [
            self._period(
                datetime(2026, 7, 20, 9, 0, tzinfo=fixed_timezone),
                5,
                "Idle",
                "Break",
                "Idle",
                "#999999",
                idle=True,
            ),
            self._period(
                datetime(2026, 7, 22, 15, 0, tzinfo=fixed_timezone),
                7,
                "Idle",
                "Away",
                "Idle",
                "#999999",
                idle=True,
            ),
        ]

        with patch(
            "timetracker.analytics.local_midnight",
            side_effect=fixed_local_midnight,
        ):
            analytics = analyze_usage(idle_periods, start_day, end_day)

        self.assertEqual(analytics.idle_seconds, 12 * 60)
        self.assertEqual(analytics.active_seconds, 0)
        self.assertEqual(analytics.average_daily_seconds, 0)
        self.assertEqual(analytics.longest_session_seconds, 0)
        self.assertEqual(analytics.categories, ())
        self.assertEqual(analytics.applications, ())
        self.assertEqual(analytics.browser_tabs, ())
        self.assertEqual(len(analytics.buckets), 3)

        for bucket in analytics.buckets:
            with self.subTest(bucket=bucket.label):
                self.assertEqual(bucket.total_seconds, 0)
                self.assertEqual(bucket.categories, ())

if __name__ == "__main__":
    unittest.main()
