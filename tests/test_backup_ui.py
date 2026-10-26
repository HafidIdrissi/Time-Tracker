from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.modules.setdefault("tkinter", mock.MagicMock())
sys.modules.setdefault("tkinter.ttk", sys.modules["tkinter"].ttk)
sys.modules.setdefault("tkinter.messagebox", sys.modules["tkinter"].messagebox)
sys.modules.setdefault("tkinter.filedialog", sys.modules["tkinter"].filedialog)

import windows_app
from timetracker.database import ActivityDatabase


class BackupDialogTests(unittest.TestCase):
    def test_selecting_source_database_shows_error_without_success(self) -> None:
        app = windows_app.TimeTrackerApp.__new__(windows_app.TimeTrackerApp)
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "activity.db"
            with ActivityDatabase(source):
                pass
            with (
                mock.patch.object(windows_app, "DATABASE_PATH", source),
                mock.patch.object(
                    windows_app.filedialog, "asksaveasfilename", return_value=str(source)
                ),
                mock.patch.object(windows_app.messagebox, "askyesno", return_value=True),
                mock.patch.object(windows_app.messagebox, "showerror") as showerror,
                mock.patch.object(windows_app.messagebox, "showinfo") as showinfo,
            ):
                app.backup_activity_database()
            showerror.assert_called_once()
            self.assertEqual(showerror.call_args.args[0], "Unable to back up")
            showinfo.assert_not_called()
            with ActivityDatabase(source) as database:
                self.assertEqual(database.recent_periods(), [])
            self.assertTrue(source.read_bytes().startswith(b"SQLite format 3"))

    def test_failed_backup_preserves_existing_destination_without_success(self) -> None:
        app = windows_app.TimeTrackerApp.__new__(windows_app.TimeTrackerApp)
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "activity.db"
            destination = Path(directory) / "backup.db"
            sentinel = b"previous backup"
            with ActivityDatabase(source):
                pass
            destination.write_bytes(sentinel)
            with (
                mock.patch.object(windows_app, "DATABASE_PATH", source),
                mock.patch.object(
                    windows_app.filedialog,
                    "asksaveasfilename",
                    return_value=str(destination),
                ),
                mock.patch.object(windows_app.messagebox, "askyesno", return_value=True),
                mock.patch.object(
                    windows_app,
                    "copy_activity_database",
                    side_effect=OSError("fixture"),
                ),
                mock.patch.object(windows_app.messagebox, "showerror") as showerror,
                mock.patch.object(windows_app.messagebox, "showinfo") as showinfo,
            ):
                app.backup_activity_database()
            self.assertEqual(destination.read_bytes(), sentinel)
            showerror.assert_called_once()
            self.assertEqual(showerror.call_args.args[0], "Unable to back up")
            showinfo.assert_not_called()


if __name__ == "__main__":
    unittest.main()
