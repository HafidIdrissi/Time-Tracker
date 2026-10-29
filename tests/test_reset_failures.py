"""Tests for desktop reset failure handling and control recovery (issue #328).

All activity is fictional. No real user data or activity titles are used.
"""
from __future__ import annotations

import queue
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

sys.modules.setdefault("tkinter", mock.MagicMock())
sys.modules.setdefault("tkinter.ttk", sys.modules["tkinter"].ttk)
sys.modules.setdefault("tkinter.messagebox", sys.modules["tkinter"].messagebox)
sys.modules.setdefault("tkinter.filedialog", sys.modules["tkinter"].filedialog)

import windows_app
from timetracker.database import ActivityDatabase
from timetracker.models import ActivityState


class FakeStringVar:
    """Lightweight StringVar stand-in for headless tests."""

    def __init__(self, value: str = "") -> None:
        self._value = str(value)

    def get(self) -> str:
        return self._value

    def set(self, value: str) -> None:
        self._value = str(value)


class FakeWidget:
    """Lightweight Tk widget stand-in for headless tests."""

    def __init__(self, state: str = "normal") -> None:
        self.state = state
        self.state_history: list[str] = [state]
        self.options: dict[str, object] = {"state": state}

    def configure(self, **kwargs: object) -> None:
        self.options.update(kwargs)
        if "state" in kwargs:
            self.state = str(kwargs["state"])
            self.state_history.append(self.state)

    def cget(self, key: str) -> object:
        if key == "state":
            return self.state
        if key in self.options:
            return self.options[key]
        raise KeyError(key)


class ResetFailureTests(unittest.TestCase):
    """Regression coverage for confirmed reset database failures and recoveries."""

    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory(prefix="time-tracker-reset-")
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name)
        self.database = self.base / "data" / "activity.db"

        patch = mock.patch.object(windows_app, "DATABASE_PATH", self.database)
        patch.start()
        self.addCleanup(patch.stop)

        for name in ("showerror", "showinfo", "askyesno"):
            patch = mock.patch.object(windows_app.messagebox, name)
            setattr(self, name, patch.start())
            self.addCleanup(patch.stop)

        self.askyesno.return_value = True

        self.app = windows_app.TimeTrackerApp.__new__(windows_app.TimeTrackerApp)
        self.app.messages = queue.Queue()
        self.app.closing = False
        self.app.root = mock.Mock()
        self.app.tracker_thread = None
        self.app.tracker = None
        self.app.stop_requested = False
        self.app.pending_reset = False
        self.app.restart_after_reset = False

        self.app.status_text = FakeStringVar("Stopped")
        self.app.status_detail = FakeStringVar("Tracking is not running")
        self.app.status_badge = FakeWidget()
        self.app.start_button = FakeWidget("normal")
        self.app.stop_button = FakeWidget("disabled")
        self.app.interval_box = FakeWidget("readonly")
        self.app.idle_box = FakeWidget("readonly")
        self.app.reset_button = FakeWidget("normal")
        self.app.reset_data_button = FakeWidget("normal")

        # Summary and detail fields updated when reset completes:
        self.app.application_text = FakeStringVar("—")
        self.app.window_text = FakeStringVar("No window detected")
        self.app.current_duration_text = FakeStringVar("00:00:00")
        self.app.tracking_duration_text = FakeStringVar("00:00:00")
        self.app.last_measure_text = FakeStringVar("—")
        self.app.live_idle_text = FakeStringVar("0 s")
        self.app.active_text = FakeStringVar("0 min")
        self.app.idle_text = FakeStringVar("0 min")
        self.app.app_count_text = FakeStringVar("0")
        self.app.period_count_text = FakeStringVar("0")
        self.app.analysis_total_text = FakeStringVar("0 min")
        self.app.analysis_average_text = FakeStringVar("0 min")
        self.app.analysis_longest_text = FakeStringVar("0 min")
        self.app.category_tree = mock.Mock()
        self.app.analysis_app_tree = mock.Mock()
        self.app.analysis_tab_tree = mock.Mock()
        self.app._show_recent_periods = mock.Mock()
        self.app._replace_tree_rows = mock.Mock()
        self.app._draw_usage_chart = mock.Mock()
        self.app.start_tracking = mock.Mock()

        self._seed_database()

    def _seed_database(self) -> None:
        """Seed disposable database with fictional rows at fixed aware timestamps."""
        t1 = datetime(2026, 7, 20, 9, 0, tzinfo=timezone.utc)
        t2 = datetime(2026, 7, 20, 9, 15, tzinfo=timezone.utc)
        t3 = datetime(2026, 7, 20, 9, 30, tzinfo=timezone.utc)
        t4 = datetime(2026, 7, 20, 9, 45, tzinfo=timezone.utc)

        with ActivityDatabase(self.database) as database:
            id1 = database.create_period(
                ActivityState("Code.exe", "Fictional code editor"), t1
            )
            database.update_period(id1, t1, t2)

            id2 = database.create_period(
                ActivityState("browser.exe", "Fictional documentation"), t2
            )
            database.update_period(id2, t2, t3)

            id3 = database.create_period(
                ActivityState("Idle", "No keyboard or mouse activity", is_idle=True), t3
            )
            database.update_period(id3, t3, t4)

    def _snapshot_rows(self) -> list[tuple[int, str, str, str, str, float, int]]:
        """Return all stored row fields, including IDs, closing the connection cleanly."""
        connection = sqlite3.connect(self.database)
        try:
            cursor = connection.execute(
                "SELECT id, application, window_title, started_at, ended_at, duration_seconds, is_idle "
                "FROM activity_periods ORDER BY id ASC"
            )
            return cursor.fetchall()
        finally:
            connection.close()

    def test_initially_stopped_reset_failure_preserves_history_and_recovers_on_retry(self) -> None:
        # Pre-operation state
        rows_before = self._snapshot_rows()
        self.assertEqual(len(rows_before), 3)
        with ActivityDatabase(self.database) as database:
            periods_before = database.all_periods()
        self.assertEqual(len(periods_before), 3)

        self.assertEqual(self.app.status_text.get(), "Stopped")
        self.assertFalse(self.app.pending_reset)
        self.assertFalse(self.app.restart_after_reset)
        self.assertEqual(str(self.app.reset_button.cget("state")), "normal")
        self.assertEqual(str(self.app.reset_data_button.cget("state")), "normal")

        # Inject failure from clear_periods before deletion occurs
        with mock.patch.object(
            ActivityDatabase,
            "clear_periods",
            side_effect=sqlite3.OperationalError("database is locked"),
        ):
            self.app.reset_activity()

        # Failure assertions: rows unchanged
        rows_after_failure = self._snapshot_rows()
        self.assertEqual(rows_after_failure, rows_before)
        with ActivityDatabase(self.database) as database:
            self.assertEqual(database.all_periods(), periods_before)

        # Both reset controls restored
        self.assertEqual(str(self.app.reset_button.cget("state")), "normal")
        self.assertEqual(str(self.app.reset_data_button.cget("state")), "normal")
        self.assertIn("disabled", self.app.reset_button.state_history)
        self.assertIn("disabled", self.app.reset_data_button.state_history)

        # Pending-reset flags cleared
        self.assertFalse(self.app.pending_reset)
        self.assertFalse(self.app.restart_after_reset)

        # Tracking remains stopped
        self.assertEqual(self.app.status_text.get(), "Stopped")

        # Error dialog shown, no success message, no scheduled restart
        self.showerror.assert_called_once_with("Unable to reset", "database is locked")
        self.showinfo.assert_not_called()
        self.app.root.after.assert_not_called()
        self.app.start_tracking.assert_not_called()

        # Retry with failure removed: explicit confirmed retry succeeds
        self.showerror.reset_mock()
        self.app.reset_activity()

        # Real clear succeeded
        self.assertEqual(self._snapshot_rows(), [])
        with ActivityDatabase(self.database) as database:
            self.assertEqual(database.all_periods(), [])

        self.showinfo.assert_called_once_with(
            "Activity history reset", "All activity data has been deleted."
        )
        self.showerror.assert_not_called()
        self.assertEqual(str(self.app.reset_button.cget("state")), "normal")
        self.assertEqual(str(self.app.reset_data_button.cget("state")), "normal")
        self.assertFalse(self.app.pending_reset)
        self.assertFalse(self.app.restart_after_reset)
        self.assertEqual(self.app.status_text.get(), "Stopped")
        self.app.start_tracking.assert_not_called()

    def test_stop_for_reset_failure_defers_preserves_history_and_recovers_on_retry(self) -> None:
        # Pre-operation state with tracking running
        rows_before = self._snapshot_rows()
        self.assertEqual(len(rows_before), 3)
        with ActivityDatabase(self.database) as database:
            periods_before = database.all_periods()
        self.assertEqual(len(periods_before), 3)

        mock_thread = mock.Mock()
        mock_thread.is_alive.return_value = True
        self.app.tracker_thread = mock_thread
        mock_tracker = mock.Mock()
        self.app.tracker = mock_tracker
        self.app.status_text.set("Running")
        self.app.status_detail.set("Tracking active · sampling every 1 second(s)")
        self.app.start_button.configure(state="disabled")
        self.app.stop_button.configure(state="normal")

        with mock.patch.object(
            ActivityDatabase,
            "clear_periods",
            side_effect=sqlite3.OperationalError("database is locked"),
        ) as mock_clear:
            # User confirms reset while tracking is active
            self.app.reset_activity()

            # Assert deletion is deferred until tracking stops
            mock_tracker.stop.assert_called_once()
            self.assertTrue(self.app.stop_requested)
            self.assertTrue(self.app.pending_reset)
            self.assertTrue(self.app.restart_after_reset)
            self.assertEqual(str(self.app.reset_button.cget("state")), "disabled")
            self.assertEqual(str(self.app.reset_data_button.cget("state")), "disabled")
            mock_clear.assert_not_called()
            self.assertEqual(self._snapshot_rows(), rows_before)
            self.showerror.assert_not_called()
            self.showinfo.assert_not_called()

            # Explicitly deliver tracker_stopped event
            mock_thread.is_alive.return_value = False
            self.app.messages.put(("tracker_stopped", None))
            self.app._process_messages()

            # Tracking status updated to stopped
            self.assertEqual(self.app.status_text.get(), "Stopped")
            self.assertEqual(self.app.status_detail.get(), "Tracking is not running")

            # Scheduled callback captured instead of sleeping
            scheduled_reset_calls = [
                args for args, _ in self.app.root.after.call_args_list
                if len(args) >= 2 and args[1] == self.app._perform_reset
            ]
            self.assertEqual(len(scheduled_reset_calls), 1)
            delay, scheduled_callback = scheduled_reset_calls[0]
            self.assertEqual(delay, 100)
            self.assertEqual(scheduled_callback, self.app._perform_reset)

            # Deletion still deferred before callback invocation
            mock_clear.assert_not_called()
            self.assertEqual(self._snapshot_rows(), rows_before)

            # Invoke scheduled reset callback
            self.app.root.after.reset_mock()
            scheduled_callback()

            # Assert clear_periods was called and failed
            mock_clear.assert_called_once()

        # Failure assertions: rows unchanged
        rows_after_failure = self._snapshot_rows()
        self.assertEqual(rows_after_failure, rows_before)
        with ActivityDatabase(self.database) as database:
            self.assertEqual(database.all_periods(), periods_before)

        # Both reset controls restored to normal
        self.assertEqual(str(self.app.reset_button.cget("state")), "normal")
        self.assertEqual(str(self.app.reset_data_button.cget("state")), "normal")

        # Pending-reset and restart flags cleared
        self.assertFalse(self.app.pending_reset)
        self.assertFalse(self.app.restart_after_reset)

        # Tracking remains stopped (must not silently restart)
        self.assertEqual(self.app.status_text.get(), "Stopped")

        # Error dialog shown, no success message, no scheduled restart
        self.showerror.assert_called_once_with("Unable to reset", "database is locked")
        self.showinfo.assert_not_called()
        self.app.root.after.assert_not_called()
        self.app.start_tracking.assert_not_called()

        # Retry with failure removed: explicit confirmed retry succeeds
        self.showerror.reset_mock()
        self.app.reset_activity()

        # Real clear succeeded
        self.assertEqual(self._snapshot_rows(), [])
        with ActivityDatabase(self.database) as database:
            self.assertEqual(database.all_periods(), [])

        self.showinfo.assert_called_once_with(
            "Activity history reset", "All activity data has been deleted."
        )
        self.showerror.assert_not_called()
        self.assertEqual(str(self.app.reset_button.cget("state")), "normal")
        self.assertEqual(str(self.app.reset_data_button.cget("state")), "normal")
        self.assertFalse(self.app.pending_reset)
        self.assertFalse(self.app.restart_after_reset)
        self.assertEqual(self.app.status_text.get(), "Stopped")
        self.app.start_tracking.assert_not_called()

    def test_initially_stopped_reset_oserror_preserves_history_and_recovers_controls(self) -> None:
        rows_before = self._snapshot_rows()
        self.assertEqual(len(rows_before), 3)

        with mock.patch.object(
            ActivityDatabase,
            "clear_periods",
            side_effect=OSError("Disk I/O error"),
        ):
            self.app.reset_activity()

        self.assertEqual(self._snapshot_rows(), rows_before)
        self.assertEqual(str(self.app.reset_button.cget("state")), "normal")
        self.assertEqual(str(self.app.reset_data_button.cget("state")), "normal")
        self.assertFalse(self.app.pending_reset)
        self.assertFalse(self.app.restart_after_reset)
        self.assertEqual(self.app.status_text.get(), "Stopped")
        self.showerror.assert_called_once_with("Unable to reset", "Disk I/O error")
        self.showinfo.assert_not_called()
        self.app.root.after.assert_not_called()
        self.app.start_tracking.assert_not_called()

        # Retry after OSError failure succeeds
        self.showerror.reset_mock()
        self.app.reset_activity()

        self.assertEqual(self._snapshot_rows(), [])
        self.showinfo.assert_called_once_with(
            "Activity history reset", "All activity data has been deleted."
        )
        self.showerror.assert_not_called()
        self.assertEqual(str(self.app.reset_button.cget("state")), "normal")
        self.assertEqual(str(self.app.reset_data_button.cget("state")), "normal")
        self.assertFalse(self.app.pending_reset)
        self.assertFalse(self.app.restart_after_reset)
        self.app.start_tracking.assert_not_called()


if __name__ == "__main__":
    unittest.main()
