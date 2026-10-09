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

    def test_stop_requested_before_run_never_samples(self) -> None:
        origin = datetime(2026, 7, 20, 8, 0, tzinfo=timezone.utc)
        clock = {"value": origin}

        def now() -> datetime:
            current = clock["value"]
            clock["value"] = current + timedelta(seconds=1)
            return current

        class CountingProvider:
            def __init__(self) -> None:
                self.calls = 0

            def sample(self) -> ActivitySnapshot:
                self.calls += 1
                raise AssertionError("The provider must not be sampled")

        provider = CountingProvider()
        with tempfile.TemporaryDirectory() as directory:
            with ActivityDatabase(Path(directory) / "activity.db") as database:
                tracker = ActivityTracker(
                    database,
                    provider,
                    poll_interval=30,
                    now=now,
                )
                tracker.stop()
                tracker.stop()
                tracker.run()
                stored = database.all_periods()

        self.assertEqual(provider.calls, 0)
        self.assertEqual(stored, [])
        self.assertEqual(clock["value"], origin + timedelta(seconds=1))

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
    def test_clock_jump_backwards_rejects_older_snapshots_and_recovers_cleanly(self) -> None:
        origin = datetime(2026, 7, 20, 10, 0, 0, tzinfo=timezone.utc)
        editor = ActivityState("Code.exe", "Editor")
        browser = ActivityState("firefox.exe", "Documentation")

        with tempfile.TemporaryDirectory() as directory:
            with ActivityDatabase(Path(directory) / "activity.db") as database:
                tracker = ActivityTracker(database, UnusedProvider())

                # 1. Normal observation up to 10:00:30
                tracker.record_snapshot(ActivitySnapshot(editor, 0), origin)
                tracker.record_snapshot(ActivitySnapshot(editor, 30), origin + timedelta(seconds=30))

                periods_before = self._periods(database, origin)
                self.assertEqual(len(periods_before), 1)
                self.assertEqual(periods_before[0].started_at, origin)
                self.assertEqual(periods_before[0].ended_at, origin + timedelta(seconds=30))
                self.assertEqual(periods_before[0].duration_seconds, 30)

                # 2. Backwards clock: snapshot at 10:00:10 must be rejected
                tracker.record_snapshot(ActivitySnapshot(browser, 0), origin + timedelta(seconds=10))

                periods_after_reject = self._periods(database, origin)
                self.assertEqual(len(periods_after_reject), 1)
                self.assertEqual(periods_after_reject[0].ended_at, origin + timedelta(seconds=30))
                self.assertEqual(periods_after_reject[0].duration_seconds, 30)

                # 3. Recovery at 10:00:35: closes editor at 10:00:35 and starts browser at 10:00:35
                tracker.record_snapshot(ActivitySnapshot(browser, 0), origin + timedelta(seconds=35))

                periods_recovered = self._periods(database, origin)
                self.assertEqual(len(periods_recovered), 2)
                self.assertEqual(periods_recovered[0].ended_at, origin + timedelta(seconds=35))
                self.assertEqual(periods_recovered[0].duration_seconds, 35)
                self.assertEqual(periods_recovered[1].started_at, origin + timedelta(seconds=35))
                self.assertEqual(periods_recovered[1].application, "firefox.exe")
    def test_failed_creation_preserves_committed_boundary_and_watermark(self) -> None:
        origin = datetime(2026, 7, 20, 10, 0, 0, tzinfo=timezone.utc)
        state_a = ActivityState("Code.exe", "Editor")
        state_b = ActivityState("firefox.exe", "Documentation")

        with tempfile.TemporaryDirectory() as directory:
            with ActivityDatabase(Path(directory) / "activity.db") as database:
                tracker = ActivityTracker(database, UnusedProvider())

                # 1. Accept A at 10:00:00, confirm through 10:00:30
                tracker.record_snapshot(ActivitySnapshot(state_a, 0), origin)
                tracker.record_snapshot(ActivitySnapshot(state_a, 0), origin + timedelta(seconds=30))

                # 2. Observe B at 10:00:35, injecting create_period failure.
                # A's update commits end=10:00:35, watermark must advance to 10:00:35.
                orig_create = database.create_period
                def failing_create(state, started_at):
                    raise RuntimeError("DB Disk Full")
                database.create_period = failing_create

                with self.assertRaises(RuntimeError):
                    tracker.record_snapshot(ActivitySnapshot(state_b, 0), origin + timedelta(seconds=35))

                self.assertEqual(tracker._state, state_a)
                self.assertEqual(tracker._watermark, origin + timedelta(seconds=35))
                periods = self._periods(database, origin)
                self.assertEqual(len(periods), 1)
                self.assertEqual(periods[0].ended_at, origin + timedelta(seconds=35))
                self.assertEqual(periods[0].duration_seconds, 35)

                # 3. Older active/idle observations at 10:00:32 must be rejected by advanced watermark
                tracker.record_snapshot(ActivitySnapshot(state_a, 0), origin + timedelta(seconds=32))
                tracker.record_snapshot(ActivitySnapshot(state_a, 200), origin + timedelta(seconds=32))
                periods = self._periods(database, origin)
                self.assertEqual(len(periods), 1)
                self.assertEqual(periods[0].ended_at, origin + timedelta(seconds=35))
                self.assertEqual(periods[0].duration_seconds, 35)

                # Backwards run() stop at 10:00:32 must preserve the committed 10:00:35 end
                tracker._now = lambda: origin + timedelta(seconds=32)
                tracker.stop()
                tracker.run()
                periods = self._periods(database, origin)
                self.assertEqual(periods[0].ended_at, origin + timedelta(seconds=35))
                self.assertEqual(periods[0].duration_seconds, 35)

                # 4. Recover on subsequent B retry at 10:00:40
                database.create_period = orig_create
                tracker.record_snapshot(ActivitySnapshot(state_b, 0), origin + timedelta(seconds=40))
                periods = self._periods(database, origin)
                self.assertEqual(len(periods), 2)
                self.assertEqual(periods[0].ended_at, origin + timedelta(seconds=40))
                self.assertEqual(periods[0].duration_seconds, 40)
                self.assertEqual(periods[1].started_at, origin + timedelta(seconds=40))

    def test_initial_create_and_update_failure_controls(self) -> None:
        origin = datetime(2026, 7, 20, 10, 0, 0, tzinfo=timezone.utc)
        state_a = ActivityState("Code.exe", "Editor")

        with tempfile.TemporaryDirectory() as directory:
            with ActivityDatabase(Path(directory) / "activity.db") as database:
                tracker = ActivityTracker(database, UnusedProvider())

                # Initial create failure: watermark and state must remain unset
                orig_create = database.create_period
                def failing_create(state, started_at):
                    raise RuntimeError("Init Create Failed")
                database.create_period = failing_create

                with self.assertRaises(RuntimeError):
                    tracker.record_snapshot(ActivitySnapshot(state_a, 0), origin)

                self.assertIsNone(tracker._state)
                self.assertIsNone(tracker._watermark)
                self.assertEqual(len(self._periods(database, origin)), 0)

                # Recover initial creation
                database.create_period = orig_create
                tracker.record_snapshot(ActivitySnapshot(state_a, 0), origin)
                self.assertEqual(tracker._state, state_a)
                self.assertEqual(tracker._watermark, origin)

                # Update failure: watermark and committed end remain unchanged
                orig_update = database.update_period
                def failing_update(period_id, started_at, ended_at):
                    raise RuntimeError("Update Failed")
                database.update_period = failing_update

                with self.assertRaises(RuntimeError):
                    tracker.record_snapshot(ActivitySnapshot(state_a, 0), origin + timedelta(seconds=10))

                self.assertEqual(tracker._watermark, origin)

                # Restore update and observe recovery
                database.update_period = orig_update
                tracker.record_snapshot(ActivitySnapshot(state_a, 0), origin + timedelta(seconds=20))
                self.assertEqual(tracker._watermark, origin + timedelta(seconds=20))
                periods = self._periods(database, origin)
                self.assertEqual(len(periods), 1)
                self.assertEqual(periods[0].ended_at, origin + timedelta(seconds=20))
                
    def test_idle_transition_clamps_to_watermark_without_overlap(self) -> None:
        origin = datetime(2026, 7, 20, 10, 0, 0, tzinfo=timezone.utc)
        active = ActivityState("Code.exe", "Editor")

        with tempfile.TemporaryDirectory() as directory:
            with ActivityDatabase(Path(directory) / "activity.db") as database:
                tracker = ActivityTracker(database, UnusedProvider())

                # Accept A at 10:00:00 and confirm through 10:00:30
                tracker.record_snapshot(ActivitySnapshot(active, 0), origin)
                tracker.record_snapshot(ActivitySnapshot(active, 0), origin + timedelta(seconds=30))

                # At 10:00:35, idle_seconds=200 with default 180s threshold (derived: 10:00:15)
                # Must clamp to 10:00:30 without overlapping confirmed activity
                tracker.record_snapshot(ActivitySnapshot(active, 200), origin + timedelta(seconds=35))

                periods = self._periods(database, origin)
                self.assertEqual(len(periods), 2)
                self.assertEqual(periods[0].ended_at, origin + timedelta(seconds=30))
                self.assertEqual(periods[0].duration_seconds, 30)
                self.assertEqual(periods[1].started_at, origin + timedelta(seconds=30))
                self.assertEqual(periods[1].ended_at, origin + timedelta(seconds=35))
                self.assertEqual(periods[1].duration_seconds, 5)

    def test_failed_creation_does_not_publish_inconsistent_state(self) -> None:
        origin = datetime(2026, 7, 20, 10, 0, 0, tzinfo=timezone.utc)
        state_a = ActivityState("Code.exe", "Editor")
        state_b = ActivityState("firefox.exe", "Documentation")

        with tempfile.TemporaryDirectory() as directory:
            with ActivityDatabase(Path(directory) / "activity.db") as database:
                tracker = ActivityTracker(database, UnusedProvider())
                tracker.record_snapshot(ActivitySnapshot(state_a,0), origin)
                tracker.record_snapshot(ActivitySnapshot(state_a,0), origin + timedelta(seconds=30))
                orig_create = database.create_period
                def failing_create(state, started_at):
                    raise RuntimeError("DB Disk Full")
                database.create_period = failing_create

                with self.assertRaises(RuntimeError):
                    tracker.record_snapshot(ActivitySnapshot(state_b, 0), origin + timedelta(seconds=35))

                self.assertEqual(tracker._state, state_a)
                periods = self._periods(database, origin)
                self.assertEqual(len(periods), 1)
                self.assertEqual(periods[0].ended_at, origin + timedelta(seconds=35))
                self.assertEqual(periods[0].duration_seconds, 35)

                # 3. Older snapshot at 10:00:32 must be rejected by advanced watermark
                tracker.record_snapshot(ActivitySnapshot(state_a, 0), origin + timedelta(seconds=32))
                periods = self._periods(database, origin)
                self.assertEqual(periods[0].ended_at, origin + timedelta(seconds=35))
                self.assertEqual(periods[0].duration_seconds, 35)

                # 4. Recover on subsequent B at 10:00:40
                database.create_period = orig_create
                tracker.record_snapshot(ActivitySnapshot(state_b, 0), origin + timedelta(seconds=40))
                periods = self._periods(database, origin)
                self.assertEqual(len(periods), 2)
                self.assertEqual(periods[0].ended_at, origin + timedelta(seconds=40))
                self.assertEqual(periods[1].started_at, origin + timedelta(seconds=40))



    def test_run_finalization_preserves_period_on_backwards_clock(self) -> None:
        origin = datetime(2026, 7, 20, 10, 0, 0, tzinfo=timezone.utc)
        editor = ActivityState("Code.exe", "Editor")

        class StepProvider:
            def __init__(self, tracker_ref: list) -> None:
                self.tracker_ref = tracker_ref
                self.calls = 0

            def sample(self) -> ActivitySnapshot:
                self.calls += 1
                if self.calls == 2:
                    self.tracker_ref[0].stop()
                return ActivitySnapshot(editor, 0)

        times = [
            origin,
            origin + timedelta(seconds=30),
            origin + timedelta(seconds=10),
        ]

        def fake_now() -> datetime:
            if times:
                return times.pop(0)
            return origin + timedelta(seconds=10)

        with tempfile.TemporaryDirectory() as directory:
            with ActivityDatabase(Path(directory) / "activity.db") as database:
                holder: list = []
                provider = StepProvider(holder)
                tracker = ActivityTracker(
                    database=database,
                    provider=provider,
                    poll_interval=0.01,
                    now=fake_now,
                )
                holder.append(tracker)
                tracker.run()

                periods = self._periods(database, origin)
                self.assertEqual(len(periods), 1)
                self.assertEqual(periods[0].started_at, origin)
                self.assertEqual(periods[0].ended_at, origin + timedelta(seconds=30))
                self.assertEqual(periods[0].duration_seconds, 30)

if __name__ == "__main__":
    unittest.main()

