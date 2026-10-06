from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from timetracker.database import ActivityDatabase
from timetracker.models import ActivitySnapshot, ActivityState
from timetracker.tracker import ActivityTracker


class UnusedProvider:
    def sample(self) -> ActivitySnapshot:
        raise AssertionError("The polling loop is not used in this test")


class TrackerTests(unittest.TestCase):
    def test_window_changes_and_idle_threshold_create_precise_periods(self) -> None:
        origin = datetime(2026, 7, 20, 8, 0, tzinfo=timezone.utc)
        editor = ActivityState("Code.exe", "Local Time Tracker")
        browser = ActivityState("firefox.exe", "Documentation")

        with tempfile.TemporaryDirectory() as directory:
            with ActivityDatabase(Path(directory) / "activity.db") as database:
                tracker = ActivityTracker(database, UnusedProvider())
                tracker.record_snapshot(ActivitySnapshot(editor, 0), origin)
                tracker.record_snapshot(
                    ActivitySnapshot(editor, 179), origin + timedelta(seconds=179)
                )
                tracker.record_snapshot(
                    ActivitySnapshot(editor, 185), origin + timedelta(seconds=185)
                )
                tracker.record_snapshot(
                    ActivitySnapshot(browser, 0), origin + timedelta(seconds=190)
                )
                tracker.record_snapshot(
                    ActivitySnapshot(browser, 5), origin + timedelta(seconds=195)
                )

                periods = database.periods_between(
                    origin - timedelta(seconds=1), origin + timedelta(minutes=10)
                )

        self.assertEqual(len(periods), 3)
        self.assertEqual(periods[0].application, "Code.exe")
        self.assertEqual(periods[0].duration_seconds, 180)
        self.assertTrue(periods[1].is_idle)
        self.assertEqual(periods[1].duration_seconds, 10)
        self.assertEqual(periods[2].application, "firefox.exe")
        self.assertEqual(periods[2].duration_seconds, 5)

    def _periods(self, database: ActivityDatabase, origin: datetime):
        return database.periods_between(
            origin - timedelta(hours=1), origin + timedelta(hours=2)
        )

    def test_repeated_active_snapshots_extend_one_period(self) -> None:
        origin = datetime(2026, 7, 20, 8, 0, tzinfo=timezone.utc)
        editor = ActivityState("Code.exe", "Editor")
        with tempfile.TemporaryDirectory() as directory:
            with ActivityDatabase(Path(directory) / "activity.db") as database:
                tracker = ActivityTracker(database, UnusedProvider(), idle_threshold=180)
                tracker.record_snapshot(ActivitySnapshot(editor, 0), origin)
                tracker.record_snapshot(ActivitySnapshot(editor, 10), origin + timedelta(seconds=25))
                tracker.record_snapshot(ActivitySnapshot(editor, 20), origin + timedelta(seconds=40))
                periods = self._periods(database, origin)
        self.assertEqual(len(periods), 1)
        self.assertEqual(periods[0].application, "Code.exe")
        self.assertEqual(periods[0].window_title, "Editor")
        self.assertFalse(periods[0].is_idle)
        self.assertEqual(periods[0].duration_seconds, 40)
        self.assertEqual(periods[0].ended_at, origin + timedelta(seconds=40))

    def test_idle_starts_at_exact_threshold(self) -> None:
        origin = datetime(2026, 7, 20, 8, 0, tzinfo=timezone.utc)
        editor = ActivityState("Code.exe", "Editor")
        with tempfile.TemporaryDirectory() as directory:
            with ActivityDatabase(Path(directory) / "activity.db") as database:
                tracker = ActivityTracker(database, UnusedProvider(), idle_threshold=180)
                tracker.record_snapshot(ActivitySnapshot(editor, 0), origin)
                tracker.record_snapshot(
                    ActivitySnapshot(editor, 180), origin + timedelta(seconds=180)
                )
                periods = self._periods(database, origin)
        self.assertEqual(len(periods), 2)
        self.assertFalse(periods[0].is_idle)
        self.assertEqual(periods[0].duration_seconds, 180)
        self.assertTrue(periods[1].is_idle)
        self.assertEqual(periods[1].started_at, origin + timedelta(seconds=180))
        self.assertEqual(periods[1].duration_seconds, 0)

    def test_return_from_idle_uses_observation_time(self) -> None:
        origin = datetime(2026, 7, 20, 8, 0, tzinfo=timezone.utc)
        editor = ActivityState("Code.exe", "Editor")
        with tempfile.TemporaryDirectory() as directory:
            with ActivityDatabase(Path(directory) / "activity.db") as database:
                tracker = ActivityTracker(database, UnusedProvider(), idle_threshold=180)
                tracker.record_snapshot(ActivitySnapshot(editor, 200), origin)
                resumed = origin + timedelta(seconds=30)
                tracker.record_snapshot(ActivitySnapshot(editor, 0), resumed)
                periods = self._periods(database, origin)
        self.assertEqual(len(periods), 2)
        self.assertTrue(periods[0].is_idle)
        self.assertEqual(periods[0].ended_at, resumed)
        self.assertEqual(periods[0].duration_seconds, 30)
        self.assertEqual(periods[1].application, "Code.exe")
        self.assertFalse(periods[1].is_idle)
        self.assertEqual(periods[1].started_at, resumed)
        self.assertEqual(periods[1].duration_seconds, 0)

    def test_application_change_has_no_idle_gap(self) -> None:
        origin = datetime(2026, 7, 20, 8, 0, tzinfo=timezone.utc)
        editor = ActivityState("Code.exe", "Editor")
        browser = ActivityState("firefox.exe", "Docs")
        with tempfile.TemporaryDirectory() as directory:
            with ActivityDatabase(Path(directory) / "activity.db") as database:
                tracker = ActivityTracker(database, UnusedProvider(), idle_threshold=180)
                tracker.record_snapshot(ActivitySnapshot(editor, 0), origin)
                changed = origin + timedelta(seconds=40)
                tracker.record_snapshot(ActivitySnapshot(browser, 0), changed)
                periods = self._periods(database, origin)
        self.assertEqual(len(periods), 2)
        self.assertEqual(periods[0].application, "Code.exe")
        self.assertEqual(periods[0].ended_at, changed)
        self.assertEqual(periods[0].duration_seconds, 40)
        self.assertEqual(periods[1].application, "firefox.exe")
        self.assertEqual(periods[1].window_title, "Docs")
        self.assertEqual(periods[1].started_at, changed)
        self.assertFalse(periods[1].is_idle)

    def test_stop_finalizes_the_current_period_once(self) -> None:
        origin = datetime(2026, 7, 20, 8, 0, tzinfo=timezone.utc)
        moments = [origin]

        def now() -> datetime:
            current = moments[0]
            moments[0] = current + timedelta(seconds=2)
            return current

        class StoppingProvider:
            def __init__(self) -> None:
                self.calls = 0
                self.tracker: ActivityTracker | None = None

            def sample(self) -> ActivitySnapshot:
                self.calls += 1
                assert self.tracker is not None
                self.tracker.stop()
                self.tracker.stop()
                return ActivitySnapshot(ActivityState("Code.exe", "Editor"), 0)

        provider = StoppingProvider()
        with tempfile.TemporaryDirectory() as directory:
            with ActivityDatabase(Path(directory) / "activity.db") as database:
                tracker = ActivityTracker(
                    database, provider, poll_interval=30, idle_threshold=180, now=now
                )
                provider.tracker = tracker
                tracker.run()
                tracker.stop()
                periods = self._periods(database, origin)
        self.assertEqual(provider.calls, 1)
        self.assertEqual(len(periods), 1)
        self.assertEqual(periods[0].application, "Code.exe")
        self.assertEqual(periods[0].duration_seconds, 2)
        self.assertGreaterEqual(periods[0].duration_seconds, 0)

    def test_idle_transition_cannot_move_before_period_start(self) -> None:
        origin = datetime(2026, 7, 20, 8, 0, tzinfo=timezone.utc)
        editor = ActivityState("Code.exe", "Editor")
        with tempfile.TemporaryDirectory() as directory:
            with ActivityDatabase(Path(directory) / "activity.db") as database:
                tracker = ActivityTracker(database, UnusedProvider(), idle_threshold=180)
                tracker.record_snapshot(ActivitySnapshot(editor, 0), origin)
                observed = origin + timedelta(seconds=10)
                tracker.record_snapshot(ActivitySnapshot(editor, 1000), observed)
                periods = self._periods(database, origin)
        self.assertEqual(len(periods), 2)
        self.assertEqual(periods[0].ended_at, origin)
        self.assertEqual(periods[0].duration_seconds, 0)
        self.assertTrue(periods[1].is_idle)
        self.assertEqual(periods[1].started_at, origin)
        self.assertEqual(periods[1].ended_at, observed)
        self.assertEqual(periods[1].duration_seconds, 10)
        self.assertGreaterEqual(periods[1].duration_seconds, 0)

    def test_run_loop_recovers_from_transient_provider_exceptions(self) -> None:
        origin = datetime(2026, 7, 20, 8, 0, tzinfo=timezone.utc)
        moments = [origin]

        def now() -> datetime:
            current = moments[0]
            moments[0] = current + timedelta(seconds=2)
            return current

        class FlakyProvider:
            def __init__(self) -> None:
                self.calls = 0
                self.tracker: ActivityTracker | None = None

            def sample(self) -> ActivitySnapshot:
                self.calls += 1
                if self.calls == 1:
                    return ActivitySnapshot(ActivityState("Code.exe", "Editor"), 0)
                elif self.calls == 2:
                    raise RuntimeError("Transient provider error")
                elif self.calls == 3:
                    return ActivitySnapshot(ActivityState("firefox.exe", "Docs"), 0)
                else:
                    assert self.tracker is not None
                    self.tracker.stop()
                    return ActivitySnapshot(ActivityState("firefox.exe", "Docs"), 0)

        provider = FlakyProvider()
        with tempfile.TemporaryDirectory() as directory:
            with ActivityDatabase(Path(directory) / "activity.db") as database:
                tracker = ActivityTracker(
                    database, provider, poll_interval=0.001, idle_threshold=180, now=now
                )
                provider.tracker = tracker
                tracker.run()
                periods = self._periods(database, origin)

        self.assertEqual(provider.calls, 4)
        self.assertEqual(len(periods), 2)
        self.assertEqual(periods[0].application, "Code.exe")
        self.assertEqual(periods[0].duration_seconds, 4)
        self.assertEqual(periods[1].application, "firefox.exe")
        self.assertEqual(periods[1].duration_seconds, 4)

    def test_constructor_rejects_invalid_settings(self) -> None:
        for setting in ("poll_interval", "idle_threshold"):
            for value in (float("nan"), float("inf"), float("-inf"), 0.0, -1.0):
                with self.subTest(setting=setting, value=value):
                    database = mock.Mock(spec=ActivityDatabase)
                    provider = mock.Mock(spec=UnusedProvider)

                    with self.assertRaisesRegex(
                        ValueError,
                        f"{setting} must be finite and greater than zero",
                    ):
                        ActivityTracker(database, provider, **{setting: value})

                    self.assertEqual(database.mock_calls, [])
                    self.assertEqual(provider.mock_calls, [])

    def test_constructor_accepts_defaults_custom_and_fractional_settings(self) -> None:
        cases = [
            ({}, 5.0, 180.0),
            ({"poll_interval": 2.0, "idle_threshold": 30.0}, 2.0, 30.0),
            ({"poll_interval": 0.5, "idle_threshold": 0.25}, 0.5, 0.25),
        ]
        for settings, interval, threshold in cases:
            with self.subTest(settings=settings):
                database = mock.Mock(spec=ActivityDatabase)
                provider = mock.Mock(spec=UnusedProvider)

                tracker = ActivityTracker(database, provider, **settings)

                self.assertEqual(tracker.poll_interval, interval)
                self.assertEqual(tracker.idle_threshold, threshold)
                self.assertEqual(database.mock_calls, [])
                self.assertEqual(provider.mock_calls, [])

if __name__ == "__main__":
    unittest.main()

