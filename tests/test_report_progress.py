"""Tests for report-generation progress and completion status (issue #136).

All activity is fictional. No real user data or activity titles are used.
"""
from __future__ import annotations

import queue
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
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

    def __init__(self) -> None:
        self.state = "normal"

    def configure(self, **kwargs) -> None:
        if "state" in kwargs:
            self.state = kwargs["state"]

    def cget(self, key: str) -> str:
        if key == "state":
            return self.state
        raise KeyError(key)


class ReportProgressTests(unittest.TestCase):
    """Validate report-generation UI status and worker queue communication."""

    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory(prefix="time-tracker-report-")
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name)
        self.database = self.base / "data" / "activity.db"
        self.reports = self.base / "reports"
        for name, value in (
            ("APP_DIRECTORY", self.base),
            ("DATABASE_PATH", self.database),
            ("REPORTS_DIRECTORY", self.reports),
        ):
            patch = mock.patch.object(windows_app, name, value)
            patch.start()
            self.addCleanup(patch.stop)

        for name in ("showerror", "showinfo", "showwarning", "askyesno"):
            patch = mock.patch.object(windows_app.messagebox, name)
            setattr(self, name, patch.start())
            self.addCleanup(patch.stop)

        patch = mock.patch.object(windows_app.os, "startfile", create=True)
        self.startfile = patch.start()
        self.addCleanup(patch.stop)

        self.app = windows_app.TimeTrackerApp.__new__(windows_app.TimeTrackerApp)
        self.app.report_date = FakeStringVar(date.today().isoformat())
        self.app.report_status_text = FakeStringVar("")
        self.app.report_button = FakeWidget()
        self.app.report_date_entry = FakeWidget()
        self.app.messages = queue.Queue()
        self.app.closing = True
        self.app.root = mock.Mock()

    def _seed(self) -> None:
        start = datetime(2026, 7, 20, 9, 0, tzinfo=timezone.utc)
        with ActivityDatabase(self.database) as database:
            identifier = database.create_period(
                ActivityState("Code.exe", "Fictional document"), start
            )
            database.update_period(
                identifier, start, start + timedelta(minutes=5)
            )

    def _process_once(self) -> None:
        """Run one round of message processing on the main thread."""
        self.app._process_messages()

    # --- 1. Successful generation ---

    def test_successful_generation_shows_path_and_restores_controls(self) -> None:
        self.app.report_date.set("2026-07-20")
        with mock.patch("threading.Thread") as thread_cls:
            self.app.generate_selected_report()
            thread_cls.assert_called_once()
            call_kwargs = thread_cls.call_args.kwargs
            self.assertEqual(call_kwargs.get("target"), self.app._report_worker)
            self.assertEqual(call_kwargs.get("args"), (date(2026, 7, 20),))

        # Busy state entered.
        self.assertEqual(self.app.report_status_text.get(), "Generating report\u2026")
        self.assertEqual(str(self.app.report_button.cget("state")), "disabled")
        self.assertEqual(str(self.app.report_date_entry.cget("state")), "disabled")

        # Simulate worker result.
        output = self.reports / "report-2026-07-20.html"
        self.app.messages.put(("report_ready", output))
        self._process_once()

        # Status shows path, controls restored, auto-open called.
        self.assertIn(str(output), self.app.report_status_text.get())
        self.assertIn("Report generated:", self.app.report_status_text.get())
        self.assertNotIn("could not open", self.app.report_status_text.get())
        self.assertEqual(str(self.app.report_button.cget("state")), "normal")
        self.assertEqual(str(self.app.report_date_entry.cget("state")), "normal")
        self.startfile.assert_called_once_with(str(output))

    # --- 2. Generation failure ---

    def test_generation_failure_shows_error_and_restores_controls(self) -> None:
        self.app.report_date.set("2026-07-20")
        with mock.patch("threading.Thread"):
            self.app.generate_selected_report()

        # Busy state entered.
        self.assertEqual(self.app.report_status_text.get(), "Generating report\u2026")

        # Simulate worker error.
        self.app.messages.put(("report_error", "database is locked"))
        self._process_once()

        status = self.app.report_status_text.get()
        self.assertIn("failed", status.lower())
        self.assertIn("database is locked", status)
        self.assertEqual(str(self.app.report_button.cget("state")), "normal")
        self.assertEqual(str(self.app.report_date_entry.cget("state")), "normal")

    # --- 3. Open failure after successful generation ---

    def test_open_failure_shows_path_with_open_warning(self) -> None:
        self.app.report_date.set("2026-07-20")
        with mock.patch("threading.Thread"):
            self.app.generate_selected_report()

        output = self.reports / "report-2026-07-20.html"
        self.startfile.side_effect = OSError("no associated application")
        self.app.messages.put(("report_ready", output))
        self._process_once()

        status = self.app.report_status_text.get()
        # Report generation is considered successful.
        self.assertIn("Report generated:", status)
        self.assertIn(str(output), status)
        # Opening failure is distinguished from generation failure.
        self.assertIn("could not open automatically", status)
        self.assertNotIn("failed", status.lower())
        # Controls restored.
        self.assertEqual(str(self.app.report_button.cget("state")), "normal")
        self.assertEqual(str(self.app.report_date_entry.cget("state")), "normal")

    # --- 4. Invalid date ---

    def test_invalid_date_does_not_enter_busy_state(self) -> None:
        self.app.report_date.set("not-a-date")
        with mock.patch("threading.Thread") as thread_cls:
            self.app.generate_selected_report()
            thread_cls.assert_not_called()

        # Warning shown, busy state NOT entered.
        self.showwarning.assert_called_once()
        self.assertEqual(self.app.report_status_text.get(), "")
        self.assertEqual(str(self.app.report_button.cget("state")), "normal")
        self.assertEqual(str(self.app.report_date_entry.cget("state")), "normal")

    # --- 5. Controls always restored ---

    def test_controls_restored_after_each_scenario(self) -> None:
        """Run multiple generations in sequence to confirm controls always recover."""
        for scenario, message in (
            ("success", ("report_ready", Path("C:/fictional/report.html"))),
            ("error", ("report_error", "fictional failure")),
        ):
            self.app.report_date.set("2026-07-20")
            with mock.patch("threading.Thread"):
                self.app.generate_selected_report()
            self.assertEqual(
                str(self.app.report_button.cget("state")),
                "disabled",
                f"button should be disabled during {scenario}",
            )
            self.assertEqual(
                str(self.app.report_date_entry.cget("state")),
                "disabled",
                f"date entry should be disabled during {scenario}",
            )
            self.app.messages.put(message)
            self._process_once()
            self.assertEqual(
                str(self.app.report_button.cget("state")),
                "normal",
                f"button not restored after {scenario}",
            )
            self.assertEqual(
                str(self.app.report_date_entry.cget("state")),
                "normal",
                f"date entry not restored after {scenario}",
            )

    # --- Worker does not touch Tk ---

    def test_worker_only_uses_queue(self) -> None:
        """Confirm _report_worker communicates via the queue, not Tk."""
        self._seed()
        config = self.base / "config.json"
        config.write_text(
            '{"default_category": "Other", "categories": []}',
            encoding="utf-8",
        )
        self.app._report_worker(date(2026, 7, 20))
        kind, payload = self.app.messages.get_nowait()
        self.assertEqual(kind, "report_ready")
        self.assertIsInstance(payload, Path)
        self.assertTrue(payload.exists())

    def test_worker_error_uses_queue(self) -> None:
        """Confirm _report_worker puts errors on the queue."""
        config = self.base / "config.json"
        config.write_text("{ invalid JSON", encoding="utf-8")
        self.app._report_worker(date(2026, 7, 20))
        kind, payload = self.app.messages.get_nowait()
        self.assertEqual(kind, "report_error")
        self.assertIsInstance(payload, str)


if __name__ == "__main__":
    unittest.main()
