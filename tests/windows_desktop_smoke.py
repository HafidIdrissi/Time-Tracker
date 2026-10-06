"""Native Windows/Tk checks, run separately from headless unittest discovery.

All activity is fictional. Dialog responses and shell opening are injected;
Tk widgets, events, SQLite, tracker/report threads and output files are real.
"""
from __future__ import annotations

import csv
import json
import os
import sys
import tempfile
import time
import tkinter as tk
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest import TestCase, main, mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import windows_app
from timetracker.database import ActivityDatabase
from timetracker.models import ActivityPeriod, ActivitySnapshot, ActivityState


class FictionalProvider:
    title = "Fictional project — initial window"

    def sample(self) -> ActivitySnapshot:
        return ActivitySnapshot(ActivityState("Code.exe", self.title), 0)


class NativeDesktopTests(TestCase):
    def setUp(self) -> None:
        self.assertEqual(sys.platform, "win32", "These checks require native Windows.")
        self.directory = tempfile.TemporaryDirectory(prefix="time-tracker-native-")
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name)
        self.database = self.base / "data" / "activity.db"
        self.reports = self.base / "reports"
        self.provider = FictionalProvider()
        self.callbacks: list[str] = []
        for name, value in (
            ("APP_DIRECTORY", self.base),
            ("DATABASE_PATH", self.database),
            ("REPORTS_DIRECTORY", self.reports),
        ):
            patch = mock.patch.object(windows_app, name, value)
            patch.start()
            self.addCleanup(patch.stop)
        patch = mock.patch.object(windows_app, "WindowsActivityProvider", return_value=self.provider)
        patch.start()
        self.addCleanup(patch.stop)
        for name in ("showerror", "showinfo", "showwarning", "askyesno"):
            patch = mock.patch.object(windows_app.messagebox, name)
            setattr(self, name, patch.start())
            self.addCleanup(patch.stop)
        self.askyesno.return_value = True
        patch = mock.patch.object(windows_app.os, "startfile")
        self.open_file = patch.start()
        self.addCleanup(patch.stop)
        self.root = tk.Tk()
        self.root.report_callback_exception = lambda exc, value, tb: self.callbacks.append(
            f"{exc.__name__}: {value}"
        )
        self.app = windows_app.TimeTrackerApp(self.root)
        self.addCleanup(self.dispose_app)
        self.root.update()
        self.wait(lambda: self.app.status_text.get() == "Running")
        self.wait(lambda: self.app.window_text.get() == self.provider.title)
        self.stop()

    def wait(self, predicate, timeout: float = 10) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.root.update()
            self.assertEqual(self.callbacks, [], "Unhandled Tk callback error")
            if predicate():
                return
            time.sleep(0.01)
        self.fail("Timed out waiting for native UI state")

    def stop(self) -> None:
        self.app.stop_tracking()
        self.wait(lambda: self.app.status_text.get() == "Stopped")
        if self.app.tracker_thread:
            self.app.tracker_thread.join(timeout=2)
            self.assertFalse(self.app.tracker_thread.is_alive())

    def dispose_app(self) -> None:
        if not self.root.winfo_exists():
            return
        self.app.stop_requested = True
        if self.app.tracker:
            self.app.tracker.stop()
        if self.app.tracker_thread:
            self.app.tracker_thread.join(timeout=5)
        self.app.closing = True
        for identifier in self.root.tk.call("after", "info"):
            self.root.after_cancel(identifier)
        # Flush ttk theme-change idle callbacks before destroying the Tcl app.
        self.root.update_idletasks()
        self.root.destroy()
        self.assertEqual(self.callbacks, [])

    def seed(self) -> None:
        start = windows_app.local_midnight(date.today()) + timedelta(seconds=1)
        with ActivityDatabase(self.database) as database:
            database.clear_periods()
            identifier = database.create_period(
                ActivityState("Code.exe", "Fictional title, comma \"quotes\" \u2603"), start
            )
            database.update_period(identifier, start, start + timedelta(minutes=5))

    def choose_destination(self, destination: Path | str, operation) -> None:
        with mock.patch.object(
            windows_app.filedialog, "asksaveasfilename", return_value=str(destination)
        ):
            operation()

    def widgets(self, parent):
        for child in parent.winfo_children():
            yield child
            yield from self.widgets(child)

    def test_tracker_titles_analysis_reports_stop_restart_and_reset(self) -> None:
        self.seed()
        self.app.start_tracking()
        self.wait(lambda: self.app.status_text.get() == "Running")
        self.provider.title = "Fictional project — changed title"
        self.wait(lambda: self.app.window_text.get() == self.provider.title)
        self.wait(lambda: self.app.current_duration_text.get() != "00:00:00", timeout=5)
        self.app._refresh_analysis(schedule=False)
        self.assertFalse(self.app.analysis_error)
        self.assertGreaterEqual(self.app.analysis_data.active_seconds, 300)
        self.app.generate_selected_report()
        report = self.reports / f"report-{date.today().isoformat()}.html"
        self.wait(lambda: report.exists() and self.open_file.called)
        self.assertIn("Fictional title", report.read_text(encoding="utf-8"))
        self.assertIn("Report generated:", self.app.report_status_text.get())
        self.assertIn(str(report), self.app.report_status_text.get())
        self.assertEqual(str(self.app.report_button.cget("state")), "normal")
        self.assertEqual(str(self.app.report_date_entry.cget("state")), "normal")
        self.showerror.assert_not_called()
        self.stop()
        self.app.start_tracking()
        self.wait(lambda: self.app.status_text.get() == "Running")
        self.stop()

        # Reset must also clear a previous failure, and keep generated HTML.
        self.app._show_analysis_error()
        self.app.reset_activity()
        with ActivityDatabase(self.database) as database:
            self.assertEqual(database.all_periods(), [])
        self.assertFalse(self.app.analysis_error)
        self.assertTrue(report.exists())
        self.assertEqual(self.app.recent_tree.get_children(), ())
        self.assertEqual(self.app.current_duration_text.get(), "00:00:00")

    def test_analysis_ranges_failure_and_recovery_with_real_config(self) -> None:
        self.seed()
        for mode in ("today", "week", "previous-week"):
            self.app.analysis_range.set(mode)
            self.app._refresh_analysis(schedule=False)
            self.assertFalse(self.app.analysis_error)
            expected_start, expected_end = windows_app.usage_analysis_range(date.today(), mode)
            label = self.app.analysis_period_text.get()
            self.assertIn(expected_end.isoformat(), label)
            if mode == "previous-week":
                self.assertIn(expected_start.isoformat(), label)
                self.assertEqual(self.app.analysis_data.active_seconds, 0)
            else:
                self.assertGreaterEqual(self.app.analysis_data.active_seconds, 300)
        self.app.analysis_range.set("today")
        config = self.base / "config.json"
        config.write_text("{ invalid JSON", encoding="utf-8")
        self.app._refresh_analysis(schedule=False)
        self.assertTrue(self.app.analysis_error)
        self.assertIsNone(self.app.analysis_data)
        self.assertEqual(self.app.analysis_total_text.get(), "—")
        for tree in (self.app.category_tree, self.app.analysis_app_tree, self.app.analysis_tab_tree):
            self.assertEqual(len(tree.get_children()), 1)
            self.assertIn("Analysis unavailable", tree.item(tree.get_children()[0], "values"))
        texts = [
            self.app.usage_canvas.itemcget(item, "text")
            for item in self.app.usage_canvas.find_all()
            if self.app.usage_canvas.type(item) == "text"
        ]
        self.assertIn("Usage analysis could not be refreshed.", texts)
        config.unlink()
        self.app._refresh_analysis(schedule=False)
        self.assertFalse(self.app.analysis_error)
        self.assertGreaterEqual(self.app.analysis_data.active_seconds, 300)

    def test_preferences_and_native_keyboard_traversal(self) -> None:
        self.app.poll_interval_text.set("2")
        self.app.idle_threshold_text.set("5")
        self.app.interval_box.event_generate("<<ComboboxSelected>>")
        self.root.update()
        self.assertEqual(
            windows_app.load_tracking_preferences(self.base / "preferences.json"), ("2", "5")
        )
        with mock.patch.object(windows_app, "save_tracking_preferences", side_effect=OSError("fixture")):
            self.app.idle_box.event_generate("<<ComboboxSelected>>")
            self.root.update()
        self.showwarning.assert_called_once()
        self.app.start_tracking()
        self.wait(lambda: self.app.status_text.get() == "Running")
        self.stop()

        notebook = self.app.notebook
        notebook.select(0)
        self.app.recent_tree.focus_force()
        self.root.update()
        self.app.recent_tree.event_generate("<Control-KeyPress-Tab>")
        self.root.update()
        self.assertEqual(notebook.index(notebook.select()), 1)
        focused = self.root.focus_get()
        focused.event_generate("<Control-Shift-KeyPress-Tab>")
        self.root.update()
        self.assertEqual(notebook.index(notebook.select()), 0)
        for key, index in (("u", 1), ("r", 2), ("d", 0)):
            self.root.event_generate(f"<Alt-KeyPress-{key}>")
            self.root.update()
            self.assertEqual(notebook.index(notebook.select()), index)
        notebook.select(2)
        self.root.update()
        entry = next(w for w in self.widgets(notebook) if isinstance(w, windows_app.ttk.Entry))
        entry.focus_force()
        self.root.update()
        expected_next = self.root.tk.call("tk_focusNext", str(entry))
        entry.event_generate("<KeyPress-Tab>")
        self.root.update()
        self.assertEqual(str(self.root.focus_get()), str(expected_next))
        self.root.focus_get().event_generate("<Shift-KeyPress-Tab>")
        self.root.update()
        self.assertEqual(str(self.root.focus_get()), str(entry))

        # A fresh app instance reads preferences rather than inheriting Tcl variables.
        self.dispose_app()
        self.root = tk.Tk()
        self.root.report_callback_exception = lambda exc, value, tb: self.callbacks.append(str(value))
        self.app = windows_app.TimeTrackerApp(self.root)
        self.assertEqual(self.app.poll_interval_text.get(), "2")
        self.assertEqual(self.app.idle_threshold_text.get(), "5")

    def test_native_tree_selection_focus_scroll_and_removed_rows(self) -> None:
        start = datetime.now().astimezone()
        periods = [
            ActivityPeriod(i, "Code.exe", f"Fictional row {i}", start, start + timedelta(minutes=1), 60, False)
            for i in range(40, 0, -1)
        ]
        tree = self.app.recent_tree
        self.app.notebook.select(0)
        self.app._show_recent_periods(periods)
        self.root.update()
        tree.selection_set("10")
        tree.focus("10")
        tree.see("10")
        self.root.update()
        self.assertGreater(tree.yview()[0], 0)
        self.app._show_recent_periods(periods)
        self.root.update()
        self.assertEqual(tree.selection(), ("10",))
        self.assertEqual(tree.focus(), "10")
        self.assertTrue(tree.bbox("10"), "Selected row should remain visible")
        tree.yview_moveto(0)
        self.app._show_recent_periods(periods)
        self.root.update()
        self.assertEqual(tree.yview()[0], 0)
        self.app._show_recent_periods([p for p in periods if p.id != 10])
        self.assertEqual(tree.selection(), ())
        self.assertFalse(tree.exists("10"))

    def test_exports_backup_cancellation_and_write_failures(self) -> None:
        self.seed()
        for kind in ("csv", "json"):
            destination = self.base / f"fictional.{kind}"
            self.choose_destination(destination, lambda: self.app.export_activity_file(kind))
            if kind == "csv":
                with destination.open(encoding="utf-8", newline="") as handle:
                    rows = list(csv.DictReader(handle))
            else:
                rows = json.loads(destination.read_text(encoding="utf-8"))
            self.assertEqual(len(rows), 1)
            self.assertIn('comma "quotes" \u2603', rows[0]["window_title"])
        self.showerror.assert_not_called()
        self.showinfo.reset_mock()
        self.choose_destination("", lambda: self.app.export_activity_file("csv"))
        self.showinfo.assert_not_called()
        self.choose_destination(self.database, lambda: self.app.export_activity_file("csv"))
        self.showerror.assert_called_once()
        self.showerror.reset_mock()
        blocked = self.base / "blocked"
        blocked.write_text("ordinary file", encoding="utf-8")
        self.choose_destination(blocked / "export.csv", lambda: self.app.export_activity_file("csv"))
        self.showerror.assert_called_once()
        self.showerror.reset_mock()

        backup = self.base / "backup.db"
        self.app.start_tracking()
        self.wait(lambda: self.app.status_text.get() == "Running")
        self.choose_destination(backup, self.app.backup_activity_database)
        with ActivityDatabase(backup) as database:
            self.assertGreaterEqual(len(database.all_periods()), 1)
            self.assertEqual(database.connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        original = backup.read_bytes()
        self.askyesno.return_value = False
        self.choose_destination(backup, self.app.backup_activity_database)
        self.assertEqual(backup.read_bytes(), original)
        self.askyesno.return_value = True
        self.choose_destination(backup, self.app.backup_activity_database)
        self.choose_destination(self.database, self.app.backup_activity_database)
        self.assertEqual(self.showerror.call_args.args[0], "Unable to back up")
        self.showerror.reset_mock()
        self.choose_destination(blocked / "backup.db", self.app.backup_activity_database)
        self.showerror.assert_called_once()
        self.showerror.reset_mock()
        self.choose_destination("", self.app.backup_activity_database)
        self.assertEqual(self.app.status_text.get(), "Running")
        self.stop()
        with ActivityDatabase(self.database) as database:
            self.assertGreaterEqual(len(database.all_periods()), 1)

        self.app.open_reports_directory()
        self.assertTrue(self.reports.is_dir())
        with mock.patch.object(windows_app.os, "startfile", side_effect=OSError("fixture")):
            self.app.open_reports_directory()
        self.showerror.assert_called_once()
        self.showerror.reset_mock()
        with mock.patch.object(windows_app, "REPORTS_DIRECTORY", blocked / "reports"):
            self.app.open_reports_directory()
        self.showerror.assert_called_once()


if __name__ == "__main__":
    main(verbosity=2)
